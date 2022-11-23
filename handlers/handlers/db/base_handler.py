import contextlib
from typing import (
    Any,
    Collection,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Set,
)

from marshmallow import ValidationError, fields
from marshmallow.fields import Field
from sqlalchemy import and_, bindparam
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import FlushError, NoResultFound

from common_utils.chunker import chunker
from common_utils.exceptions import (
    DBException,
    DBNotFoundException,
    DBValidationException,
)
from connectors.db_connector import DEFAULT_ISOLATION_LEVEL, get_db_session_scope
from db_models import BaseDBModel
from handlers.db.serialization import BaseDBSchema


class BaseDBHandler:
    model: BaseDBModel
    schema: BaseDBSchema
    BATCH_SIZE: int = 100
    ISOLATION_LEVEL: str = DEFAULT_ISOLATION_LEVEL

    @classmethod
    @contextlib.contextmanager
    def begin_session(cls, readonly: bool = False):
        with get_db_session_scope(
            readonly=readonly, isolation_level=cls.ISOLATION_LEVEL
        ) as session:
            yield session

    @classmethod
    def _flush(cls, session: Session):
        try:
            session.flush()
        except (IntegrityError, FlushError) as e:
            raise DBException(e) from e

    @classmethod
    def bulk_insert(cls, items: List[Dict]):
        with cls.begin_session() as session:
            items_inserted = 0
            for chunk in chunker(items, cls.BATCH_SIZE):
                session.execute(cls.model.__table__.insert(), chunk)
                items_inserted += len(chunk)
            return items_inserted

    @classmethod
    def bulk_update(
        cls,
        **values: Dict[int, Any],
    ):
        """
        Example:
            bulk_update(
                some_field={1: "bar", 2: "baz"},
                other_field={1: True, 2: False}
            )
        """
        table = cls.model.__table__
        stmt = (
            table.update()
            .where(table.c.id == bindparam("_id"))
            .values(**{field: bindparam(field) for field in values})
        )
        pks = {pk for pk_values in values.values() for pk in pk_values.keys()}
        with cls.begin_session() as session:
            cls.__bulk_update_chunk(pks=pks, values=values, session=session, stmt=stmt)

    @classmethod
    def __bulk_update_chunk(
        cls, pks: Set[int], values: Dict, session: Session, stmt: Any
    ):
        for chunk in chunker(pks, cls.BATCH_SIZE):
            chunk = [
                {
                    "_id": pk,
                    **{
                        field: field_values[pk]
                        for field, field_values in values.items()
                        if pk in field_values
                    },
                }
                for pk in chunk
            ]
            session.execute(stmt, chunk)

    @classmethod
    def _serialize_one(cls, query):
        try:
            return cls.schema.dump(query.one(), many=False)
        except NoResultFound as e:
            raise DBNotFoundException(
                f"Could not find one item for table {cls.model.__name__}"
            ) from e

    @classmethod
    def get_by(cls, output_columns: Optional[List[str]] = None, **kwargs) -> Dict:
        with cls.begin_session(readonly=True) as session:
            query = cls._query_model_with_filtered_columns(
                output_columns=output_columns, session=session
            )
            query = query.filter_by(**kwargs)
            return cls._serialize_one(query=query)

    @classmethod
    def try_get_by(cls, output_columns: Optional[List[str]] = None, **kwargs):
        with contextlib.suppress(DBNotFoundException):
            return cls.get_by(output_columns=output_columns, **kwargs)

    @classmethod
    def find_in(
        cls,
        output_columns: Optional[Iterable[str]] = None,
        **filters: Collection[Any],
    ) -> Iterable[Dict]:
        """Find elements by the column with values present in the given list.
        Examples:
            >>> cls.find_in(unit_id=[1, 2, 3], output_columns=["id"])
        """
        with cls.begin_session(readonly=True) as session:
            query = cls._query_model_with_filtered_columns(
                output_columns=output_columns, session=session
            )
            for entity in (
                query.filter(
                    *[
                        getattr(cls.model, filter_name).in_(filter_group)
                        for filter_name, filter_group in filters.items()
                    ]
                )
                .enable_eagerloads(False)
                .yield_per(cls.BATCH_SIZE)
            ):
                yield cls.schema.dump(entity)

    @classmethod
    def _query_model_with_filtered_columns(
        cls, session: Session, output_columns: Optional[Iterable[str]] = None
    ):
        if output_columns is None:
            query = session.query(cls.model)
        else:
            query = session.query(
                *tuple(
                    getattr(cls.model, column_output)
                    for column_output in output_columns
                )
            )
        return query

    @classmethod
    def find(
        cls, output_columns: Optional[List[str]] = None, special_filter=None, **kwargs
    ) -> List[Dict]:
        with cls.begin_session(readonly=True) as session:
            query = cls._query_model_with_filtered_columns(
                output_columns=output_columns, session=session
            )
            # Add special SQL filtering, like, _in, etc.
            if special_filter:
                query = query.filter(*special_filter)

            return cls.schema.dump(query.filter_by(**kwargs).all(), many=True)

    @classmethod
    def find_iter(
        cls, output_columns: Optional[List[str]] = None, special_filter=None, **kwargs
    ) -> Iterator[Dict]:
        with cls.begin_session(readonly=True) as session:
            query = cls._query_model_with_filtered_columns(
                output_columns=output_columns, session=session
            )
            # Add special SQL filtering, like, _in, etc.
            if special_filter:
                query = query.filter(*special_filter)

            for entity in (
                query.filter_by(**kwargs)
                .enable_eagerloads(False)
                .yield_per(cls.BATCH_SIZE)
            ):
                yield cls.schema.dump(entity)

    @classmethod
    def find_ids(cls, **kwargs) -> list[int]:
        with cls.begin_session(readonly=True) as session:
            return [
                entity.id for entity in session.query(cls.model.id).filter_by(**kwargs)
            ]

    @classmethod
    def add(cls, **kwargs) -> Dict[str, Any]:
        with cls.begin_session() as session:
            item = cls._load(data=kwargs, instance=cls.model(), session=session)
            session.add(item)
            session.enable_relationship_loading(item)
            cls._flush(session)
            return cls.schema.dump(item)

    @classmethod
    def delete_in(cls, **kwargs):
        """Deletes all the rows matching the kwargs sent as collections of items

        Examples:
            >>> cls.delete_in(plan_id=[3])
        """
        with cls.begin_session() as session:
            table = cls.model.__table__

            session.execute(
                table.delete().where(
                    and_(
                        getattr(table.c, key).in_(value)
                        for key, value in kwargs.items()
                    )
                )
            )

    @classmethod
    def delete(cls, item_pk: Dict[str, Any]):
        """Deletes items by the primary id."""
        with cls.begin_session() as session:
            primary_keys = cls._filter_non_primary_keys(item_pk)
            item = session.query(cls.model).get(primary_keys)

            if item:
                # NOTE: here we need the try catch as assuming auto_flush is True
                # as the after delete trigger could issue some query
                # invoked auto flushes which could raise IntegrityErrors
                try:
                    session.delete(item)
                    cls._flush(session)
                    return cls.schema.dump(item)
                except (FlushError, IntegrityError) as e:
                    raise DBException(e) from e
            else:
                raise DBNotFoundException(
                    f"No result found for {cls.model.__name__} with {item_pk}"
                )

    @classmethod
    def upsert(cls, new_values: Dict[str, Any], **keys) -> Dict[str, Any]:
        with cls.begin_session() as session:
            item = session.query(cls.model).filter_by(**keys).one_or_none()
            if not item:
                new_values.update(keys)
                item = cls.model()
            item = cls._load(
                data=new_values,
                session=session,
                instance=item,
                partial=True,
            )
            session.add(item)
            cls._flush(session)
            return cls.schema.dump(item)

    @classmethod
    def update(
        cls, item_pks: Dict[str, Any], new_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an item in the DB with new_values.

        Args:
            item_pks (dict): a dict with the primary keys of the item to
                update.
            new_values (dict): key, values to update over the target entity.

        Returns:
            dict: Serialised model after update.
        """
        with cls.begin_session() as session:
            item = session.query(cls.model).get(cls._filter_non_primary_keys(item_pks))
            if item:
                item = cls._load(
                    data=new_values,
                    session=session,
                    instance=item,
                    partial=True,
                )
                cls._flush(session)
                return cls.schema.dump(item)

            raise DBNotFoundException(
                f"Item for table {cls.model.__name__} does not exist for pk: {item_pks}"
            )

    @classmethod
    def exists(cls, **kwargs):
        with cls.begin_session(readonly=True) as session:
            exists_query = session.query(cls.model).filter_by(**kwargs).exists()
            return session.query(exists_query).scalar()

    @classmethod
    def _get_model_pks(cls):
        return [x.name for x in inspect(cls.model).primary_key]

    @classmethod
    def _filter_non_primary_keys(cls, item_pks):
        try:
            primary_keys = [item_pks[pk] for pk in cls._get_model_pks()]
        except KeyError as e:
            raise KeyError(
                "Missing primary key %s to update/get model %s.", e, cls.model.__name__
            ) from e
        return primary_keys

    @classmethod
    def _load(cls, **kwargs):
        try:
            return cls.schema.load(**kwargs)
        except ValidationError as e:
            raise DBValidationException(e.messages) from e


class SheetFieldMixin(Field):
    """This extension is a hack to deal with null values sent as empty strings or single spaces"""

    def __init__(self, **metadata):
        super().__init__(**metadata)
        self._load_as_none = [" ", ""]

    def _deserialize(
        self,
        value: Any,
        attr: Optional[str],
        data: Optional[Mapping[str, Any]],
        **kwargs,
    ):
        if value in self._load_as_none:
            return None
        return super(SheetFieldMixin, self)._deserialize(value, attr, data, **kwargs)


class Float(SheetFieldMixin, fields.Float):
    pass


class Int(SheetFieldMixin, fields.Int):
    pass


class Str(SheetFieldMixin, fields.Str):
    pass
