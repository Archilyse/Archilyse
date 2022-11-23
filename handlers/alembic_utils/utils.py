import contextlib
from glob import glob
from os import path
from typing import Dict, List, Optional

from alembic import command, op
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.dialects.postgresql import ENUM

from common_utils.constants import SQUASHED_MIGRATION

alembic_cfg = Config()
scripts_folder = path.dirname((path.abspath(__file__)))
alembic_cfg.set_main_option("script_location", scripts_folder)
script = ScriptDirectory.from_config(alembic_cfg)


def alembic_table_exists():
    from connectors.db_connector import get_db_session_scope

    with get_db_session_scope(readonly=True) as session:
        return session.execute("SELECT to_regclass('alembic_version');").first()[0]


def check_no_pending_migrations():
    """
    Raises EmtpyException if there are changes in the SqlALCHEMY models not reflected in alembic migrations
    """

    class EmptyException(Exception):
        pass

    class OkException(Exception):
        pass

    def raise_if_pending_migrations(migration_context, rev, generated_revisions):
        if generated_revisions[0].upgrade_ops.is_empty():
            raise OkException()
        raise EmptyException(
            f"There are changes in the models not reflected in the alembic"
            f" scripts: {generated_revisions[0].upgrade_ops.as_diffs()}"
        )

    with contextlib.suppress(OkException):
        command.revision(
            alembic_cfg,
            autogenerate=True,
            process_revision_directives=raise_if_pending_migrations,
        )


def check_scripts_do_not_have_conflicts(squashed_migration=SQUASHED_MIGRATION):
    """
    Checks whether there is a conflict between migrations with different PRs being merged
    """
    if latest_revision_in_scripts(squashed_migration=squashed_migration) + 1 != len(
        get_all_script_files()
    ):
        raise Exception(
            f"Conflicts found in the alembic migration scripts."
            f"There are {script.get_current_head()} revisions "
            f"ids and {len(get_all_script_files())} files."
        )


def latest_revision_in_scripts(squashed_migration):
    current_head = int(script.get_current_head())
    if squashed_migration:
        return current_head - squashed_migration
    return current_head


def generate_migration_script():
    rev_id = get_next_id()
    command.revision(alembic_cfg, autogenerate=True, rev_id=rev_id, message="")


def format_revision(rev_id):
    """
    Args:
        rev_id (Union[int, str]):

    Returns:
        str
    """
    if (
        isinstance(rev_id, int)
        or rev_id not in {"base", "head"}
        and not rev_id.startswith("0")
    ):
        return f"0{rev_id}"
    return rev_id


def get_next_id():
    all_files = get_all_script_files()
    if all_files:
        rev_id = max(int(path.basename(x).split("_")[0]) for x in all_files)
        rev_id += 1
    else:
        rev_id = 0
    rev_id = format_revision(rev_id)
    return rev_id


def get_all_script_files():
    versions_folder = path.join(scripts_folder, "versions/*.py")
    return glob(versions_folder)


def alembic_upgrade_head():
    command.upgrade(alembic_cfg, revision="head")


def downgrade_version(revision):
    revision = format_revision(revision)
    command.downgrade(alembic_cfg, revision=revision)


def alembic_downgrade_base():
    downgrade_version(revision="base")


def update_enum(
    existing_enum_name: str,
    new_enum_values: List[str],
    tables_and_columns: Dict[str, List[str]],
    new_enum_name: Optional[str] = None,
    update_values_queries: Optional[List[str]] = None,
    is_userroles_enum: Optional[bool] = False,
    is_array: Optional[bool] = False,
):
    """
    updating userroles enum has to be treated differently
    as in addition to the db Enum we also created a table
    containing exactly the values taken from the db Enum
    """
    import sqlalchemy as sa

    if is_userroles_enum:
        op.drop_constraint("userroles_role_name_fkey", "userroles", type_="foreignkey")

    new_enum_name = new_enum_name or existing_enum_name
    # change data type to string
    for table_name, column_names in tables_and_columns.items():
        for column_name in column_names:
            if is_array:
                op.alter_column(
                    table_name,
                    column_name,
                    type_=sa.String(),
                    nullable=True,
                    postgresql_using=f"array_to_string({column_name}, ',')",
                )
            else:
                op.alter_column(
                    table_name, column_name, type_=sa.String(), nullable=False
                )

    update_values_queries = update_values_queries or []
    for update_query in update_values_queries:
        op.execute(update_query)

    # drop and recreate enum type
    op.execute(f"DROP TYPE {existing_enum_name};")
    new_enum = ENUM(*new_enum_values, name=new_enum_name, create_type=True)
    new_enum.create(op.get_bind())

    if is_userroles_enum:
        op.execute("delete from roles")
        for value in new_enum_values:
            op.execute(f"insert into roles values ('{value}')")

    # alter column data types
    for table_name, column_names in tables_and_columns.items():
        for column_name in column_names:
            if is_array:
                op.execute(
                    f"ALTER TABLE {table_name} ALTER COLUMN {column_name}"
                    f" TYPE {new_enum_name}[] USING string_to_array({column_name}, ',')::{new_enum_name}[];"
                )
            else:
                op.execute(
                    f"ALTER TABLE {table_name} ALTER COLUMN {column_name}"
                    f" TYPE {new_enum_name} USING {column_name}::{new_enum_name};"
                )

    if is_userroles_enum:
        op.create_foreign_key(
            "userroles_role_name_fkey",
            "userroles",
            "roles",
            ["role_name"],
            ["name"],
        )
