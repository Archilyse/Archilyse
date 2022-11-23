from datetime import datetime

from celery import states
from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    VARCHAR,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PickleType,
    PrimaryKeyConstraint,
    Sequence,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType, PasswordType, generic_repr

from brooks.classifications import CLASSIFICATIONS
from brooks.types import AllAreaTypes, OpeningType, SeparatorType
from brooks.utils import (
    get_default_element_height,
    get_default_element_lower_edge,
    get_default_element_upper_edge,
)
from common_utils.competition_constants import CompetitionFeatures
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    CURRENCY,
    DMS_PERMISSION,
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
    TASK_TYPE,
    UNIT_USAGE,
    USER_ROLE,
    get_slam_version,
)
from connectors.db_connector import BaseDBModel


class BaseDatesDBMixin:
    created = Column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )  # noqa: W0108
    updated = Column(
        DateTime, onupdate=lambda: datetime.utcnow(), nullable=True
    )  # noqa: W0108


class BaseDBMixin(BaseDatesDBMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)


# Many to Many rel
class CompetitionSitesDBModel(BaseDBModel):
    __table__ = Table(
        "competition_sites",
        BaseDBModel.metadata,
        Column(
            "site_id",
            Integer,
            ForeignKey("sites.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
        Column(
            "competition_id",
            Integer,
            ForeignKey("competition.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )


class StatsMixin:
    mean = Column(Float, nullable=False)
    min = Column(Float, nullable=False)
    max = Column(Float, nullable=False)
    stddev = Column(Float, nullable=False)
    count = Column(Float, nullable=False)
    median = Column(Float, nullable=True)
    p20 = Column(Float, nullable=True)
    p80 = Column(Float, nullable=True)


@generic_repr
class PotentialSimulationDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "potential_simulations"

    __table_args__ = (
        Index(
            "idx_potential_simulations_building_footprint_gist",
            "building_footprint",
            postgresql_using="gist",
        ),
    )

    floor_number = Column(Integer, nullable=False)
    source_surr = Column(
        Enum(SURROUNDING_SOURCES), nullable=False, default=SURROUNDING_SOURCES.SWISSTOPO
    )
    region = Column(Enum(REGION), nullable=False)
    type = Column(Enum(SIMULATION_TYPE), nullable=False)
    simulation_version = Column(Enum(SIMULATION_VERSION), nullable=False)
    layout_mode = Column(Enum(POTENTIAL_LAYOUT_MODE), nullable=False)
    identifier = Column(String, nullable=True)
    building_footprint = Column(Geometry("POLYGON", spatial_index=False))
    status = Column(
        Enum(POTENTIAL_SIMULATION_STATUS),
        nullable=False,
        default=POTENTIAL_SIMULATION_STATUS.PENDING,
    )
    result = Column(JSONB, nullable=True)


@generic_repr
class ClientDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "clients"

    name = Column(String, nullable=False, unique=True)
    logo_gcs_link = Column(String, nullable=True)
    option_dxf = Column(Boolean, default=True, nullable=False)
    option_pdf = Column(Boolean, default=True, nullable=False)
    option_analysis = Column(Boolean, default=True, nullable=False)
    option_competition = Column(Boolean, default=False, nullable=False)
    option_ifc = Column(Boolean, default=True, nullable=False)

    sites = relationship("SiteDBModel", back_populates="client", cascade="delete")


@generic_repr
class ExpectedClientDataDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "expected_client_data"
    __table_args__ = (UniqueConstraint("client_id", "site_id", "client_site_id"),)
    client_site_id = Column(String, nullable=True)
    site_id = Column(Integer, nullable=True)
    client_id = Column(Integer, nullable=False)
    data = Column(JSONB(none_as_null=False), nullable=True)


@generic_repr
class SiteDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "sites"
    __table_args__ = (UniqueConstraint("client_id", "client_site_id"),)

    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    group_id = Column(
        Integer,
        ForeignKey("groups.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    name = Column(String, nullable=False)
    client_site_id = Column(String, nullable=True)
    georef_region = Column(Enum(REGION), nullable=False)
    region = Column(String, nullable=False)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    site_plan_file = Column(String, nullable=True)
    raw_dir = Column(String, nullable=True)

    full_slam_results = Column(
        Enum(ADMIN_SIM_STATUS), nullable=False, default=ADMIN_SIM_STATUS.UNPROCESSED
    )
    pipeline_and_qa_complete = Column(Boolean, nullable=False, default=False)
    heatmaps_qa_complete = Column(Boolean, nullable=False, default=False)
    basic_features_status = Column(
        Enum(ADMIN_SIM_STATUS), nullable=False, default=ADMIN_SIM_STATUS.UNPROCESSED
    )
    sample_surr_task_state = Column(
        Enum(ADMIN_SIM_STATUS), nullable=False, default=ADMIN_SIM_STATUS.UNPROCESSED
    )
    basic_features_error = Column(JSON, nullable=True)
    qa_validation = Column(JSON, nullable=True)
    validation_notes = Column(String, nullable=True)
    delivered = Column(Boolean, nullable=True, default=False)
    priority = Column(SmallInteger, nullable=False, default=1)
    simulation_version = Column(Enum(SIMULATION_VERSION), nullable=False)
    old_editor = Column(Boolean, nullable=False, default=False)
    sub_sampling_number_of_clusters = Column(Integer, nullable=True)

    gcs_buildings_link = Column(String, nullable=True)
    gcs_ifc_file_links = Column(JSON, nullable=True)
    ifc_import_status = Column(Enum(ADMIN_SIM_STATUS), nullable=True)
    ifc_import_exceptions = Column(JSON, nullable=True)
    classification_scheme = Column(
        Enum(CLASSIFICATIONS),
        nullable=False,
        default=CLASSIFICATIONS.UNIFIED,
    )

    labels = Column(ARRAY(String))

    competition = relationship(
        "CompetitionDBModel", secondary=CompetitionSitesDBModel.__table__
    )
    group = relationship("GroupDBModel")
    client = relationship("ClientDBModel", back_populates="sites")
    buildings = relationship("BuildingDBModel", back_populates="site", cascade="delete")
    enforce_masterplan = Column(Boolean, nullable=False, default=True)


@generic_repr
class BuildingDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "buildings"
    __table_args__ = (
        UniqueConstraint(
            "site_id", "street", "housenumber", name="unique_building_address"
        ),
        UniqueConstraint(
            "site_id",
            "client_building_id",
            name="unique_client_building_id",
        ),
    )

    site_id = Column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    client_building_id = Column(String, nullable=True)
    housenumber = Column(String, nullable=False)
    city = Column(String, nullable=False)
    zipcode = Column(String, nullable=False)
    street = Column(String, nullable=False)
    elevation = Column(Float, nullable=True)
    elevation_override = Column(Float, nullable=True)
    triangles_gcs_link = Column(String, nullable=True)

    labels = Column(ARRAY(String))

    site = relationship(
        "SiteDBModel",
        back_populates="buildings",
    )
    floors = relationship(
        "FloorDBModel",
        back_populates="building",
        cascade="delete",
    )
    plans = relationship(
        "PlanDBModel",
        back_populates="building",
        cascade="delete",
    )


@generic_repr
class PlanDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("image_hash", "building_id"),)

    site_id = Column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    building_id = Column(
        Integer,
        ForeignKey("buildings.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    default_wall_height = Column(
        Float,
        nullable=False,
        default=get_default_element_height(SeparatorType.WALL),
    )
    default_door_height = Column(
        Float,
        nullable=False,
        default=get_default_element_height(OpeningType.DOOR),
    )
    default_window_lower_edge = Column(
        Float,
        nullable=False,
        default=get_default_element_lower_edge(element_type=OpeningType.WINDOW),
    )
    default_window_upper_edge = Column(
        Float,
        nullable=False,
        default=get_default_element_upper_edge(element_type=OpeningType.WINDOW),
    )
    default_ceiling_slab_height = Column(
        Float,
        nullable=False,
        default=get_default_element_height(element_type="CEILING_SLAB"),
    )
    georef_x = Column(Float)
    georef_y = Column(Float)
    georef_scale = Column(Float)
    georef_rot_angle = Column(Float)
    georef_rot_x = Column(Float)
    georef_rot_y = Column(Float)
    image_hash = Column(String, nullable=False)

    image_mime_type = Column(String(255), nullable=False)
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    image_gcs_link = Column(String, nullable=False)
    area_overlay_image_gcs_link = Column(String, nullable=True)

    annotation_finished = Column(Boolean, nullable=False, default=False)

    floors = relationship("FloorDBModel", back_populates="plan", cascade="delete")
    building = relationship("BuildingDBModel", back_populates="plans")
    annotations = relationship(
        "AnnotationDBModel", back_populates="plan", uselist=False, cascade="delete"
    )
    without_units = Column(Boolean, nullable=False, default=False)
    is_masterplan = Column(Boolean, nullable=False, default=False)


class UnitsAreasDBModel(BaseDBModel):
    __table__ = Table(
        "unit_areas",
        BaseDBModel.metadata,
        Column(
            "unit_id",
            Integer,
            ForeignKey("units.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            index=True,
        ),
        Column(
            "area_id",
            Integer,
            ForeignKey("areas.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            index=True,
        ),
        Column("labels", ARRAY(String)),
    )


@generic_repr
class AreaDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "areas"
    plan_id = Column(
        Integer,
        ForeignKey("plans.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    coord_x = Column(Float, nullable=False)
    coord_y = Column(Float, nullable=False)
    area_type = Column(Enum(AllAreaTypes), nullable=False)
    scaled_polygon = Column(Text, nullable=False)

    plan = relationship("PlanDBModel")
    units = relationship("UnitDBModel", secondary=UnitsAreasDBModel.__table__)


@generic_repr
class AnnotationDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "annotations"
    __table_args__ = (UniqueConstraint("plan_id"),)

    plan_id = Column(
        Integer,
        ForeignKey("plans.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    data = Column(JSONB)

    user = relationship("UserDBModel")
    plan = relationship("PlanDBModel", back_populates="annotations")


userrole_table = Table(
    "userroles",
    BaseDBModel.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    Column("role_name", Enum(USER_ROLE), ForeignKey("roles.name"), primary_key=True),
)


class UserDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email"),
        UniqueConstraint("login"),
        UniqueConstraint("name"),
    )

    last_login = Column(DateTime(timezone=True), nullable=True)
    name = Column(String(255), unique=True)
    login = Column(String(255), unique=True, nullable=False)
    email = Column(EmailType, unique=True, nullable=False)
    email_validated = Column(Boolean, default=False, nullable=False)
    password = Column(PasswordType(schemes=["pbkdf2_sha512"]), nullable=False)
    group_id = Column(
        Integer,
        ForeignKey(
            column="groups.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    client_id = Column(
        Integer,
        ForeignKey(column="clients.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    roles = relationship("RoleDBModel", secondary=lambda: userrole_table, lazy="joined")
    group = relationship("GroupDBModel")


class RoleDBModel(BaseDBModel):
    __tablename__ = "roles"
    name = Column(Enum(USER_ROLE), primary_key=True)
    users = relationship(
        "UserDBModel", secondary=lambda: userrole_table, overlaps="roles"
    )


class GroupDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "groups"
    name = Column(String(255), unique=True, nullable=False)
    users = relationship("UserDBModel", cascade="delete", overlaps="group")


@generic_repr
class FloorDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("building_id", "floor_number"),)

    plan_id = Column(
        Integer,
        ForeignKey(column="plans.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    building_id = Column(
        Integer,
        ForeignKey(column="buildings.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    floor_number = Column(Integer, nullable=False, index=True)
    georef_z = Column(Float, nullable=True)
    gcs_en_floorplan_link = Column(String, nullable=True)
    gcs_de_floorplan_link = Column(String, nullable=True)
    gcs_fr_floorplan_link = Column(String, nullable=True)
    gcs_it_floorplan_link = Column(String, nullable=True)
    gcs_en_dxf_link = Column(String, nullable=True)
    gcs_de_dxf_link = Column(String, nullable=True)
    gcs_fr_dxf_link = Column(String, nullable=True)
    gcs_it_dxf_link = Column(String, nullable=True)
    gcs_en_pdf_link = Column(String, nullable=True)
    gcs_de_pdf_link = Column(String, nullable=True)
    gcs_fr_pdf_link = Column(String, nullable=True)
    gcs_it_pdf_link = Column(String, nullable=True)

    labels = Column(ARRAY(String))

    plan = relationship("PlanDBModel", back_populates="floors")
    building = relationship("BuildingDBModel", back_populates="floors")
    units = relationship(
        "UnitDBModel", back_populates="floor", cascade="delete"
    )  # Only parent emit delete operations, as here the Floor is father of Unit


@generic_repr
class UnitDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("site_id", "floor_id", "plan_id", "apartment_no"),
    )

    floor_id = Column(
        Integer,
        ForeignKey(column="floors.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    site_id = Column(
        Integer,
        ForeignKey(column="sites.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    plan_id = Column(
        Integer,
        ForeignKey(column="plans.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    apartment_no = Column(Integer, nullable=False)

    client_id = Column(String, nullable=True)

    ph_net_area = Column(Float, nullable=True)
    ph_final_gross_rent_annual_m2 = Column(Float, nullable=True)
    ph_final_gross_rent_adj_factor = Column(Float, nullable=True)

    ph_final_sale_price_m2 = Column(Float, nullable=True)
    ph_final_sale_price_adj_factor = Column(Float, nullable=True)

    unit_type = Column(String, nullable=True)
    unit_usage = Column(
        Enum(UNIT_USAGE), nullable=False, default=UNIT_USAGE.RESIDENTIAL
    )

    # TODO: Make this a dynamic mixin
    gcs_en_floorplan_link = Column(String, nullable=True)
    gcs_de_floorplan_link = Column(String, nullable=True)
    gcs_fr_floorplan_link = Column(String, nullable=True)
    gcs_it_floorplan_link = Column(String, nullable=True)
    gcs_en_pdf_link = Column(String, nullable=True)
    gcs_de_pdf_link = Column(String, nullable=True)
    gcs_fr_pdf_link = Column(String, nullable=True)
    gcs_it_pdf_link = Column(String, nullable=True)

    labels = Column(ARRAY(String))

    representative_unit_client_id = Column(String, nullable=True)

    floor = relationship("FloorDBModel", back_populates="units")
    areas = relationship(
        "AreaDBModel", secondary=UnitsAreasDBModel.__table__, overlaps="units"
    )


class SlamSimulationDBModel(BaseDBModel, BaseDatesDBMixin):
    __tablename__ = "slam_simulations"
    run_id = Column(String, nullable=False, primary_key=True)
    site_id = Column(
        Integer,
        ForeignKey("sites.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(Enum(TASK_TYPE), nullable=False)
    state = Column(
        Enum(ADMIN_SIM_STATUS), nullable=False, default=ADMIN_SIM_STATUS.UNPROCESSED
    )
    errors = Column(JSON, nullable=True)


class UnitStatsDBModel(BaseDBModel, StatsMixin):
    __tablename__ = "unit_statistics"
    __table_args__ = (
        ForeignKeyConstraint(
            columns=("run_id", "unit_id"),
            refcolumns=[
                "slam_unit_simulations.run_id",
                "slam_unit_simulations.unit_id",
            ],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    run_id = Column(String, nullable=False, primary_key=True)
    unit_id = Column(Integer, nullable=False, primary_key=True, index=True)
    dimension = Column(String, nullable=False, primary_key=True)
    # Exclude classification_scheme.BALCONY_AREAS from the stats
    only_interior = Column(Boolean, nullable=False, default=False, primary_key=True)


class ApartmentStatsDBModel(BaseDBModel, StatsMixin):
    __tablename__ = "apartment_statistics"

    run_id = Column(
        String,
        ForeignKey(
            column="slam_simulations.run_id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        primary_key=True,
    )
    client_id = Column(String, nullable=False, primary_key=True)
    dimension = Column(String, nullable=False, primary_key=True)
    # Exclude classification_scheme.BALCONY_AREAS from the stats
    only_interior = Column(Boolean, nullable=False, default=False, primary_key=True)


class UnitAreaStatsDBModel(BaseDBModel, StatsMixin):
    __tablename__ = "unit_area_statistics"
    __table_args__ = (
        ForeignKeyConstraint(
            columns=("run_id", "unit_id"),
            refcolumns=[
                "slam_unit_simulations.run_id",
                "slam_unit_simulations.unit_id",
            ],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        Index("idx_unit_area_statistics_run_id_unit_id", "run_id", "unit_id"),
        ForeignKeyConstraint(
            columns=("unit_id", "area_id"),
            refcolumns=["unit_areas.unit_id", "unit_areas.area_id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        Index("idx_unit_area_statistics_unit_id_area_id", "unit_id", "area_id"),
    )
    run_id = Column(String, nullable=False, primary_key=True)
    unit_id = Column(Integer, nullable=False, primary_key=True, index=True)
    area_id = Column(Integer, nullable=False, primary_key=True, index=True)
    dimension = Column(String, nullable=False, primary_key=True)


class UnitSimulationDBModel(BaseDBModel):
    __tablename__ = "slam_unit_simulations"

    run_id = Column(
        String,
        ForeignKey(
            column="slam_simulations.run_id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        primary_key=True,
    )
    unit_id = Column(
        Integer,
        ForeignKey(column="units.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
        index=True,
    )
    results = Column(JSONB(none_as_null=False), nullable=False)


class CompetitionFeaturesDBModel(BaseDBModel, BaseDatesDBMixin):
    __tablename__ = "competition_features"
    run_id = Column(
        String,
        ForeignKey(
            column="slam_simulations.run_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        primary_key=True,
    )
    results = Column(JSONB(none_as_null=False), nullable=False)


@generic_repr
class CompetitionDBModel(BaseDBModel):
    __tablename__ = "competition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        Integer,
        ForeignKey(column="clients.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name = Column(String)
    weights = Column(JSON, nullable=False)
    configuration_parameters = Column(JSONB, nullable=True)
    red_flags_enabled = Column(Boolean, default=True, nullable=False)
    currency = Column(Enum(CURRENCY), default=CURRENCY.CHF, nullable=False)
    prices_are_rent = Column(Boolean, default=True, nullable=False)
    features_selected = Column(
        ARRAY(Enum(CompetitionFeatures)),
        nullable=True,
    )

    competitors = relationship(
        "SiteDBModel",
        secondary=CompetitionSitesDBModel.__table__,
        overlaps="competition",
    )


@generic_repr
class CompetitionClientInputDBModel(BaseDBModel, BaseDatesDBMixin):
    __tablename__ = "competition_client_input"
    __table_args__ = (PrimaryKeyConstraint("competitor_id", "competition_id"),)

    competitor_id = Column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    competition_id = Column(
        Integer,
        ForeignKey("competition.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    features = Column(JSONB, nullable=False)


@generic_repr
class CeleryTaskMetaDBModel(BaseDBModel):
    __tablename__ = "celery_taskmeta"
    __table_args__ = {"extend_existing": True}

    id = Column(
        Integer,
        Sequence("task_id_sequence"),
        primary_key=True,
        autoincrement=True,
    )
    task_id = Column(String(155), unique=True)
    status = Column(String(50), default=states.PENDING)
    result = Column(PickleType, nullable=True)
    date_done = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )
    traceback = Column(Text, nullable=True)
    slam_version = Column(String, nullable=True, onupdate=get_slam_version)


@generic_repr
class CeleryTaskSetMetaDBModel(BaseDBModel):
    __tablename__ = "celery_tasksetmeta"
    __table_args__ = {"extend_existing": True}

    id = Column(
        Integer, Sequence("taskset_id_sequence"), autoincrement=True, primary_key=True
    )
    taskset_id = Column(String(155), unique=True)
    result = Column(PickleType, nullable=True)
    date_done = Column(DateTime, default=datetime.utcnow, nullable=True)
    slam_version = Column(String, nullable=True, onupdate=get_slam_version)


class FileAssociationsMixin:
    # File association
    @declared_attr
    def client_id(self):
        return Column(
            Integer,
            ForeignKey(
                "clients.id",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=False,
        )

    @declared_attr
    def site_id(self):
        return Column(
            Integer,
            ForeignKey(
                "sites.id",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=True,
        )

    @declared_attr
    def building_id(self):
        return Column(
            Integer,
            ForeignKey(
                "buildings.id",
                ondelete="SET NULL",
                onupdate="CASCADE",
            ),
            nullable=True,
        )

    @declared_attr
    def floor_id(self):
        return Column(
            Integer,
            ForeignKey(
                "floors.id",
                ondelete="SET NULL",
                onupdate="CASCADE",
            ),
            nullable=True,
        )

    @declared_attr
    def unit_id(self):
        return Column(
            Integer,
            ForeignKey(
                "units.id",
                ondelete="SET NULL",
                onupdate="CASCADE",
            ),
            nullable=True,
        )

    @declared_attr
    def creator_id(self):
        return Column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
            nullable=True,
        )

    @declared_attr
    def area_id(self):
        return Column(Integer, nullable=True)


@generic_repr
class FileDBModel(BaseDBModel, BaseDBMixin, FileAssociationsMixin):
    __tablename__ = "file"
    __table_args__ = (
        Index(
            "idx_file_all_id_and_name",
            "client_id",
            "site_id",
            "building_id",
            "floor_id",
            "unit_id",
            "area_id",
            "name",
        ),
        Index(
            "idx_file_folder_id",
            "folder_id",
        ),
        Index("idx_file_client_id_checksum", "client_id", "checksum"),
        ForeignKeyConstraint(
            columns=("area_id", "unit_id"),
            name="fk_file_unit_areas",
            refcolumns=["unit_areas.area_id", "unit_areas.unit_id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        Index("idx_file_area_id", "area_id", "unit_id"),
        Index("idx_deleted", "deleted", "updated"),
    )
    folder_id = Column(
        Integer,
        ForeignKey(
            "folder.id", ondelete="CASCADE", onupdate="CASCADE", name="file_folder_fkey"
        ),
        nullable=True,
    )

    name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=True)
    checksum = Column(String, nullable=False)

    labels = Column(ARRAY(String))
    comments = relationship("FileCommentDBModel", lazy="joined", cascade="delete")

    deleted = Column(Boolean, nullable=True, default=False)


@generic_repr
class FileCommentDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "file_comment"
    __table_args__ = (Index("idx_file_comment_file_id", "file_id"),)

    creator_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    file_id = Column(
        Integer,
        ForeignKey("file.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    comment = Column(String, nullable=False)

    creator = relationship("UserDBModel", lazy="joined")


@generic_repr
class FolderDBModel(BaseDBModel, BaseDBMixin, FileAssociationsMixin):
    __tablename__ = "folder"
    __table_args__ = (
        ForeignKeyConstraint(
            columns=("area_id", "unit_id"),
            refcolumns=["unit_areas.area_id", "unit_areas.unit_id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        Index("idx_folder_area_id", "unit_id", "area_id"),
    )

    parent_folder_id = Column(
        Integer,
        ForeignKey("folder.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    name = Column(String, nullable=False)
    labels = Column(ARRAY(String), nullable=True)
    deleted = Column(Boolean, nullable=True, default=False)


@generic_repr
class SpatialRefSys(BaseDBModel):
    __tablename__ = "spatial_ref_sys"
    __table_args__ = (
        CheckConstraint(
            "(srid > 0) AND (srid <= 998999)", name="spatial_ref_sys_srid_check"
        ),
        PrimaryKeyConstraint("srid", name="spatial_ref_sys_pkey"),
    )
    srid = Column(Integer, autoincrement=False, nullable=False)
    auth_srid = Column(Integer, autoincrement=False, nullable=True)
    auth_name = Column(VARCHAR(length=256), autoincrement=False, nullable=True)
    srtext = Column(VARCHAR(length=2048), autoincrement=False, nullable=True)
    proj4text = Column(VARCHAR(length=2048), autoincrement=False, nullable=True)


class DmsPermissionModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "dms_permissions"
    __table_args__ = (UniqueConstraint("user_id", "site_id"),)

    site_id = Column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    rights = Column(Enum(DMS_PERMISSION), nullable=False, default=False)


@generic_repr
class ReactPlannerProjectDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "react_planner_projects"

    plan_id = Column(
        Integer,
        ForeignKey("plans.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    data = Column(JSON)


class SlamSimulationValidationDBModel(BaseDBModel, BaseDatesDBMixin):
    __tablename__ = "slam_simulation_validation"

    site_id = Column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    results = Column(JSONB(none_as_null=False), nullable=False)


class ManualSurroundingsDBModel(BaseDBModel, BaseDatesDBMixin):
    __tablename__ = "manual_surroundings"
    site_id = Column(
        Integer,
        ForeignKey(
            "sites.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="manual_surroundings_site_id_fkey",
        ),
        nullable=False,
        primary_key=True,
    )
    surroundings = Column(JSONB, nullable=False)


class ClusteringSubsamplingDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "clustering_subsample"
    site_id = Column(
        Integer,
        ForeignKey(
            "sites.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="clustering_subsample_site_id_fkey",
        ),
        nullable=False,
        primary_key=False,
    )
    results = Column(JSONB(none_as_null=False), nullable=False)


class BulkVolumeProgressDBModel(BaseDBModel, BaseDBMixin):
    __tablename__ = "bulk_volume_progress"
    lk25_index = Column(Integer, nullable=False)
    lk25_subindex_2 = Column(Integer, nullable=False)
    state = Column(Enum(ADMIN_SIM_STATUS), nullable=False)
    errors = Column(JSON, nullable=True)


class PotentialCHProgress(BaseDBModel, BaseDatesDBMixin):
    __tablename__ = "potential_ch_progress"
    x = Column(Integer, nullable=False, primary_key=True)
    y = Column(Integer, nullable=False, primary_key=True)
