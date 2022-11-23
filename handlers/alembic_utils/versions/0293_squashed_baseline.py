"""

Revision ID: 0292
Revises:
Create Date: 2022-11-14 10:57:59.502729

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

from alembic_utils.enums import (
    admin_sim_status_enum,
    area_type_enum,
    classifications_enum,
    competition_features_enum,
    currency_enum,
    dms_permission_enum,
    potential_layout_enum,
    potential_simulation_status_enum,
    region_enum,
    simulation_type_enum,
    simulation_version_enum,
    surrounding_sources_enum,
    task_type_enum,
    unit_usage_enum,
    userrole_enum,
)

# revision identifiers, used by Alembic.
revision = "0293"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE SEQUENCE IF NOT EXISTS task_id_sequence START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS taskset_id_sequence START 1")

    op.create_table(
        "celery_taskmeta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=155), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("result", sa.PickleType(), nullable=True),
        sa.Column("date_done", sa.DateTime(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("slam_version", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_table(
        "celery_tasksetmeta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("taskset_id", sa.String(length=155), nullable=True),
        sa.Column("result", sa.PickleType(), nullable=True),
        sa.Column("date_done", sa.DateTime(), nullable=True),
        sa.Column("slam_version", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("taskset_id"),
    )
    op.create_table(
        "clients",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("logo_gcs_link", sa.String(), nullable=True),
        sa.Column("option_dxf", sa.Boolean(), nullable=False),
        sa.Column("option_pdf", sa.Boolean(), nullable=False),
        sa.Column("option_analysis", sa.Boolean(), nullable=False),
        sa.Column("option_competition", sa.Boolean(), nullable=False),
        sa.Column("option_ifc", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "expected_client_data",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_site_id", sa.String(), nullable=True),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "site_id", "client_site_id"),
    )
    op.create_table(
        "groups",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "bulk_volume_progress",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lk25_index", sa.Integer(), nullable=False),
        sa.Column("lk25_subindex_2", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            admin_sim_status_enum,
            nullable=False,
        ),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "roles",
        sa.Column(
            "name",
            userrole_enum,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "competition",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column(
            "configuration_parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("red_flags_enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "currency",
            currency_enum,
            nullable=False,
        ),
        sa.Column("prices_are_rent", sa.Boolean(), nullable=False),
        sa.Column(
            "features_selected",
            postgresql.ARRAY(competition_features_enum),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sites",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("client_site_id", sa.String(), nullable=True),
        sa.Column(
            "georef_region",
            region_enum,
            nullable=False,
        ),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("site_plan_file", sa.String(), nullable=True),
        sa.Column("raw_dir", sa.String(), nullable=True),
        sa.Column(
            "full_slam_results",
            admin_sim_status_enum,
            nullable=False,
        ),
        sa.Column("pipeline_and_qa_complete", sa.Boolean(), nullable=False),
        sa.Column("heatmaps_qa_complete", sa.Boolean(), nullable=False),
        sa.Column(
            "basic_features_status",
            admin_sim_status_enum,
            nullable=False,
        ),
        sa.Column(
            "sample_surr_task_state",
            admin_sim_status_enum,
            nullable=False,
        ),
        sa.Column("basic_features_error", sa.JSON(), nullable=True),
        sa.Column("qa_validation", sa.JSON(), nullable=True),
        sa.Column("validation_notes", sa.String(), nullable=True),
        sa.Column("delivered", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.SmallInteger(), nullable=False),
        sa.Column(
            "simulation_version",
            simulation_version_enum,
            nullable=False,
        ),
        sa.Column("old_editor", sa.Boolean(), nullable=False),
        sa.Column("sub_sampling_number_of_clusters", sa.Integer(), nullable=True),
        sa.Column("gcs_buildings_link", sa.String(), nullable=True),
        sa.Column("gcs_ifc_file_links", sa.JSON(), nullable=True),
        sa.Column(
            "ifc_import_status",
            admin_sim_status_enum,
            nullable=True,
        ),
        sa.Column("ifc_import_exceptions", sa.JSON(), nullable=True),
        sa.Column(
            "classification_scheme",
            classifications_enum,
            nullable=False,
        ),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("enforce_masterplan", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "client_site_id"),
    )
    op.create_table(
        "users",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column(
            "email", sqlalchemy_utils.types.email.EmailType(length=255), nullable=False
        ),
        sa.Column("email_validated", sa.Boolean(), nullable=False),
        sa.Column(
            "password",
            sqlalchemy_utils.types.password.PasswordType(
                max_length=1137, schemes=["pbkdf2_sha512"]
            ),
            nullable=False,
        ),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("login"),
        sa.UniqueConstraint("login"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "buildings",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("client_building_id", sa.String(), nullable=True),
        sa.Column("housenumber", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("zipcode", sa.String(), nullable=False),
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("elevation", sa.Float(), nullable=True),
        sa.Column("elevation_override", sa.Float(), nullable=True),
        sa.Column("triangles_gcs_link", sa.String(), nullable=True),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_id", "client_building_id", name="unique_client_building_id"
        ),
        sa.UniqueConstraint(
            "site_id", "street", "housenumber", name="unique_building_address"
        ),
    )
    op.create_table(
        "clustering_subsample",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name="clustering_subsample_site_id_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "competition_client_input",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("competitor_id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["competition_id"],
            ["competition.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["competitor_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("competitor_id", "competition_id"),
    )
    op.create_table(
        "competition_sites",
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["competition_id"],
            ["competition.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("site_id", "competition_id"),
    )
    op.create_table(
        "dms_permissions",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "rights",
            dms_permission_enum,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "site_id"),
    )
    op.create_index(
        op.f("ix_dms_permissions_user_id"), "dms_permissions", ["user_id"], unique=False
    )
    op.create_table(
        "manual_surroundings",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column(
            "surroundings", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name="manual_surroundings_site_id_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("site_id"),
    )
    op.create_table(
        "potential_ch_progress",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("x", "y"),
    )
    op.create_table(
        "potential_simulations",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "source_surr",
            surrounding_sources_enum,
            nullable=False,
        ),
        sa.Column(
            "region",
            region_enum,
            nullable=False,
        ),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            simulation_type_enum,
            nullable=False,
        ),
        sa.Column(
            "simulation_version",
            simulation_version_enum,
            nullable=False,
        ),
        sa.Column(
            "layout_mode",
            potential_layout_enum,
            nullable=False,
        ),
        sa.Column("identifier", sa.String(), nullable=True),
        sa.Column(
            "building_footprint",
            Geometry(
                geometry_type="POLYGON",
                from_text="ST_GeomFromEWKT",
                name="geometry",
                spatial_index=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "status",
            potential_simulation_status_enum,
            nullable=False,
        ),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_potential_simulations_building_footprint_gist",
        "potential_simulations",
        ["building_footprint"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_table(
        "slam_simulation_validation",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("site_id"),
    )
    op.create_table(
        "slam_simulations",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            task_type_enum,
            nullable=False,
        ),
        sa.Column(
            "state",
            admin_sim_status_enum,
            nullable=False,
        ),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_table(
        "userroles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role_name",
            userrole_enum,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_name"],
            ["roles.name"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_name"),
    )
    op.create_table(
        "apartment_statistics",
        sa.Column("mean", sa.Float(), nullable=False),
        sa.Column("min", sa.Float(), nullable=False),
        sa.Column("max", sa.Float(), nullable=False),
        sa.Column("stddev", sa.Float(), nullable=False),
        sa.Column("count", sa.Float(), nullable=False),
        sa.Column("median", sa.Float(), nullable=True),
        sa.Column("p20", sa.Float(), nullable=True),
        sa.Column("p80", sa.Float(), nullable=True),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("dimension", sa.String(), nullable=False),
        sa.Column("only_interior", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["slam_simulations.run_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("run_id", "client_id", "dimension", "only_interior"),
    )
    op.create_table(
        "competition_features",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["slam_simulations.run_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_table(
        "plans",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.Column("default_wall_height", sa.Float(), nullable=False),
        sa.Column("default_door_height", sa.Float(), nullable=False),
        sa.Column("default_window_lower_edge", sa.Float(), nullable=False),
        sa.Column("default_window_upper_edge", sa.Float(), nullable=False),
        sa.Column("default_ceiling_slab_height", sa.Float(), nullable=False),
        sa.Column("georef_x", sa.Float(), nullable=True),
        sa.Column("georef_y", sa.Float(), nullable=True),
        sa.Column("georef_scale", sa.Float(), nullable=True),
        sa.Column("georef_rot_angle", sa.Float(), nullable=True),
        sa.Column("georef_rot_x", sa.Float(), nullable=True),
        sa.Column("georef_rot_y", sa.Float(), nullable=True),
        sa.Column("image_hash", sa.String(), nullable=False),
        sa.Column("image_mime_type", sa.String(length=255), nullable=False),
        sa.Column("image_width", sa.Integer(), nullable=False),
        sa.Column("image_height", sa.Integer(), nullable=False),
        sa.Column("image_gcs_link", sa.String(), nullable=False),
        sa.Column("area_overlay_image_gcs_link", sa.String(), nullable=True),
        sa.Column("annotation_finished", sa.Boolean(), nullable=False),
        sa.Column("without_units", sa.Boolean(), nullable=False),
        sa.Column("is_masterplan", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["building_id"], ["buildings.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_hash", "building_id"),
    )
    op.create_index(
        op.f("ix_plans_building_id"), "plans", ["building_id"], unique=False
    )
    op.create_table(
        "annotations",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id"),
    )
    op.create_table(
        "areas",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("coord_x", sa.Float(), nullable=False),
        sa.Column("coord_y", sa.Float(), nullable=False),
        sa.Column(
            "area_type",
            area_type_enum,
            nullable=False,
        ),
        sa.Column("scaled_polygon", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_areas_plan_id"), "areas", ["plan_id"], unique=False)
    op.create_table(
        "floors",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column("georef_z", sa.Float(), nullable=True),
        sa.Column("gcs_en_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_de_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_fr_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_it_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_en_dxf_link", sa.String(), nullable=True),
        sa.Column("gcs_de_dxf_link", sa.String(), nullable=True),
        sa.Column("gcs_fr_dxf_link", sa.String(), nullable=True),
        sa.Column("gcs_it_dxf_link", sa.String(), nullable=True),
        sa.Column("gcs_en_pdf_link", sa.String(), nullable=True),
        sa.Column("gcs_de_pdf_link", sa.String(), nullable=True),
        sa.Column("gcs_fr_pdf_link", sa.String(), nullable=True),
        sa.Column("gcs_it_pdf_link", sa.String(), nullable=True),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(
            ["building_id"], ["buildings.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building_id", "floor_number"),
    )
    op.create_index(
        op.f("ix_floors_floor_number"), "floors", ["floor_number"], unique=False
    )
    op.create_index(op.f("ix_floors_plan_id"), "floors", ["plan_id"], unique=False)
    op.create_table(
        "react_planner_projects",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_react_planner_projects_plan_id"),
        "react_planner_projects",
        ["plan_id"],
        unique=False,
    )
    op.create_table(
        "units",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("floor_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("apartment_no", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=True),
        sa.Column("ph_net_area", sa.Float(), nullable=True),
        sa.Column("ph_final_gross_rent_annual_m2", sa.Float(), nullable=True),
        sa.Column("ph_final_gross_rent_adj_factor", sa.Float(), nullable=True),
        sa.Column("ph_final_sale_price_m2", sa.Float(), nullable=True),
        sa.Column("ph_final_sale_price_adj_factor", sa.Float(), nullable=True),
        sa.Column("unit_type", sa.String(), nullable=True),
        sa.Column(
            "unit_usage",
            unit_usage_enum,
            nullable=False,
        ),
        sa.Column("gcs_en_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_de_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_fr_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_it_floorplan_link", sa.String(), nullable=True),
        sa.Column("gcs_en_pdf_link", sa.String(), nullable=True),
        sa.Column("gcs_de_pdf_link", sa.String(), nullable=True),
        sa.Column("gcs_fr_pdf_link", sa.String(), nullable=True),
        sa.Column("gcs_it_pdf_link", sa.String(), nullable=True),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("representative_unit_client_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["floor_id"], ["floors.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site_id", "floor_id", "plan_id", "apartment_no"),
    )
    op.create_table(
        "slam_unit_simulations",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["slam_simulations.run_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"], ["units.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("run_id", "unit_id"),
    )
    op.create_index(
        op.f("ix_slam_unit_simulations_unit_id"),
        "slam_unit_simulations",
        ["unit_id"],
        unique=False,
    )
    op.create_table(
        "unit_areas",
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(
            ["area_id"], ["areas.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"], ["units.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("unit_id", "area_id"),
    )
    op.create_index(
        op.f("ix_unit_areas_area_id"), "unit_areas", ["area_id"], unique=False
    )
    op.create_index(
        op.f("ix_unit_areas_unit_id"), "unit_areas", ["unit_id"], unique=False
    )
    op.create_table(
        "folder",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_folder_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("deleted", sa.Boolean(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=True),
        sa.Column("area_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["area_id", "unit_id"],
            ["unit_areas.area_id", "unit_areas.unit_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["building_id"], ["buildings.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"], ["users.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["floor_id"], ["floors.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["parent_folder_id"], ["folder.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"], ["units.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_folder_area_id", "folder", ["unit_id", "area_id"], unique=False
    )
    op.create_table(
        "unit_area_statistics",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("dimension", sa.String(), nullable=False),
        sa.Column("mean", sa.Float(), nullable=False),
        sa.Column("min", sa.Float(), nullable=False),
        sa.Column("max", sa.Float(), nullable=False),
        sa.Column("median", sa.Float(), nullable=True),
        sa.Column("stddev", sa.Float(), nullable=False),
        sa.Column("count", sa.Float(), nullable=False),
        sa.Column("p20", sa.Float(), nullable=True),
        sa.Column("p80", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id", "unit_id"],
            ["slam_unit_simulations.run_id", "slam_unit_simulations.unit_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["unit_id", "area_id"],
            ["unit_areas.unit_id", "unit_areas.area_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("run_id", "unit_id", "area_id", "dimension"),
    )
    op.create_index(
        "idx_unit_area_statistics_run_id_unit_id",
        "unit_area_statistics",
        ["run_id", "unit_id"],
        unique=False,
    )
    op.create_index(
        "idx_unit_area_statistics_unit_id_area_id",
        "unit_area_statistics",
        ["unit_id", "area_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_unit_area_statistics_area_id"),
        "unit_area_statistics",
        ["area_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_unit_area_statistics_unit_id"),
        "unit_area_statistics",
        ["unit_id"],
        unique=False,
    )
    op.create_table(
        "unit_statistics",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("dimension", sa.String(), nullable=False),
        sa.Column("only_interior", sa.Boolean(), nullable=False),
        sa.Column("mean", sa.Float(), nullable=False),
        sa.Column("min", sa.Float(), nullable=False),
        sa.Column("max", sa.Float(), nullable=False),
        sa.Column("stddev", sa.Float(), nullable=False),
        sa.Column("count", sa.Float(), nullable=False),
        sa.Column("median", sa.Float(), nullable=True),
        sa.Column("p20", sa.Float(), nullable=True),
        sa.Column("p80", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id", "unit_id"],
            ["slam_unit_simulations.run_id", "slam_unit_simulations.unit_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("run_id", "unit_id", "dimension", "only_interior"),
    )
    op.create_index(
        op.f("ix_unit_statistics_unit_id"), "unit_statistics", ["unit_id"], unique=False
    )
    op.create_table(
        "file",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(), nullable=False),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("deleted", sa.Boolean(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=True),
        sa.Column("area_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["area_id", "unit_id"],
            ["unit_areas.area_id", "unit_areas.unit_id"],
            name="fk_file_unit_areas",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["building_id"], ["buildings.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"], ["users.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["floor_id"], ["floors.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folder.id"],
            name="file_folder_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"], ["units.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_file_all_id_and_name",
        "file",
        [
            "client_id",
            "site_id",
            "building_id",
            "floor_id",
            "unit_id",
            "area_id",
            "name",
        ],
        unique=False,
    )
    op.create_index("idx_file_area_id", "file", ["area_id", "unit_id"], unique=False)
    op.create_index(
        "idx_file_client_id_checksum", "file", ["client_id", "checksum"], unique=False
    )
    op.create_index("idx_file_folder_id", "file", ["folder_id"], unique=False)
    op.create_table(
        "file_comment",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["creator_id"], ["users.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["file_id"], ["file.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_file_comment_file_id", "file_comment", ["file_id"], unique=False
    )
    op.create_index("idx_deleted", "file", ["deleted", "updated"], unique=False)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION separators_area(project_id numeric)
        RETURNS TABLE (
                total_wall_areas numeric
        ) AS $func$
        BEGIN
           return query select (
           sum(
                ST_AREA(
                    ST_UnaryUnion(
                        ST_GeomFromGeoJSON(
                            format(
                                '{"type":"POLYGON",
                                 "coordinates": %s,
                                 "crs":{"type":"name","properties":{"name":"EPSG:3857"}}}',
                                 lines.value->'coordinates'
                            )
                        )
                    )
                )
           )
           *
           (
                select (data->'scale')::jsonb::numeric * power(0.01, 2)
                 from react_planner_projects
                 where react_planner_projects.id = project_id
           )
           )::numeric as total_wall_areas
                from react_planner_projects,
                jsonb_each((react_planner_projects.data->'layers'->'layer-1'->'lines')::jsonb) as lines
                where id = project_id
                and lines.value->>'type' != 'area_splitter';
        END ; $func$ LANGUAGE 'plpgsql';
        """
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_file_comment_file_id", table_name="file_comment")
    op.drop_table("file_comment")
    op.drop_index("idx_file_folder_id", table_name="file")
    op.drop_index("idx_file_client_id_checksum", table_name="file")
    op.drop_index("idx_file_area_id", table_name="file")
    op.drop_index("idx_file_all_id_and_name", table_name="file")
    op.drop_index("idx_deleted", table_name="file")
    op.drop_table("file")
    op.drop_index(op.f("ix_unit_statistics_unit_id"), table_name="unit_statistics")
    op.drop_table("unit_statistics")
    op.drop_index(
        op.f("ix_unit_area_statistics_unit_id"), table_name="unit_area_statistics"
    )
    op.drop_index(
        op.f("ix_unit_area_statistics_area_id"), table_name="unit_area_statistics"
    )
    op.drop_index(
        "idx_unit_area_statistics_unit_id_area_id", table_name="unit_area_statistics"
    )
    op.drop_index(
        "idx_unit_area_statistics_run_id_unit_id", table_name="unit_area_statistics"
    )
    op.drop_table("unit_area_statistics")
    op.drop_index("idx_folder_area_id", table_name="folder")
    op.drop_table("folder")
    op.drop_index(op.f("ix_unit_areas_unit_id"), table_name="unit_areas")
    op.drop_index(op.f("ix_unit_areas_area_id"), table_name="unit_areas")
    op.drop_table("unit_areas")
    op.drop_index(
        op.f("ix_slam_unit_simulations_unit_id"), table_name="slam_unit_simulations"
    )
    op.drop_table("slam_unit_simulations")
    op.drop_table("units")
    op.drop_index(
        op.f("ix_react_planner_projects_plan_id"), table_name="react_planner_projects"
    )
    op.drop_table("react_planner_projects")
    op.drop_index(op.f("ix_floors_plan_id"), table_name="floors")
    op.drop_index(op.f("ix_floors_floor_number"), table_name="floors")
    op.drop_table("floors")
    op.drop_index(op.f("ix_areas_plan_id"), table_name="areas")
    op.drop_table("areas")
    op.drop_table("annotations")
    op.drop_index(op.f("ix_plans_building_id"), table_name="plans")
    op.drop_table("plans")
    op.drop_table("competition_features")
    op.drop_table("apartment_statistics")
    op.drop_table("userroles")
    op.drop_table("slam_simulations")
    op.drop_table("slam_simulation_validation")
    op.drop_table("manual_surroundings")
    op.drop_index(op.f("ix_dms_permissions_user_id"), table_name="dms_permissions")
    op.drop_table("dms_permissions")
    op.drop_table("competition_sites")
    op.drop_table("competition_client_input")
    op.drop_table("clustering_subsample")
    op.drop_table("buildings")
    op.drop_table("users")
    op.drop_table("sites")
    op.drop_table("competition")
    op.drop_table("roles")
    op.drop_index(
        "idx_potential_simulations_building_footprint_gist",
        table_name="potential_simulations",
        postgresql_using="gist",
    )
    op.drop_table("potential_simulations")
    op.drop_table("potential_ch_progress")
    op.drop_table("groups")
    op.drop_table("expected_client_data")
    op.drop_table("clients")
    op.drop_table("celery_tasksetmeta")
    op.drop_table("celery_taskmeta")
    op.drop_table("bulk_volume_progress")

    op.execute("DROP FUNCTION IF EXISTS separators_area;")
    op.execute("DROP SEQUENCE IF EXISTS task_id_sequence, taskset_id_sequence;")

    for value in globals().values():
        if isinstance(value, sa.Enum):
            op.execute(f"DROP TYPE IF EXISTS {value.name};")
