from .base_handler import BaseDBHandler  # isort:skip
from .apartment_stats_handler import ApartmentStatsDBHandler
from .area_handler import AreaDBHandler, UnitAreaDBHandler
from .building_handler import BuildingDBHandler
from .bulk_volume_progress_handler import BulkVolumeProgressDBHandler
from .client_handler import ClientDBHandler
from .clustering_subsampling_handler import ClusteringSubsamplingDBHandler
from .competition.competition_client_input import CompetitionManualInputDBHandler
from .competition.competition_features_db_handler import CompetitionFeaturesDBHandler
from .competition.competition_handler import CompetitionDBHandler
from .dms_permission_handler import DmsPermissionDBHandler
from .file_handler import FileCommentDBHandler, FileDBHandler
from .floor_handler import FloorDBHandler
from .folder_handler import FolderDBHandler
from .group_handler import GroupDBHandler
from .manual_surroundings_handler import ManualSurroundingsDBHandler
from .plan_handler import PlanDBHandler
from .potential_simulation_handler import PotentialSimulationDBHandler
from .qa_handler import QADBHandler
from .react_planner_projects_handler import ReactPlannerProjectsDBHandler
from .role_handler import RoleDBHandler
from .site_handler import SiteDBHandler
from .slam_simulation_handler import SlamSimulationDBHandler
from .slam_simulation_validation import SlamSimulationValidationDBHandler
from .unit_area_stats_handler import UnitAreaStatsDBHandler
from .unit_handler import UnitDBHandler
from .unit_simulation_handler import UnitSimulationDBHandler
from .unit_stats_handler import UnitStatsDBHandler
from .user_handler import UserDBHandler
from .utils import (
    POTENTIAL_DB_WAIT_STRATEGY,
    apply_retry_on_operational_errors,
    get_db_handlers,
)

__all__ = (
    AreaDBHandler.__name__,
    UnitAreaDBHandler.__name__,
    ClientDBHandler.__name__,
    SiteDBHandler.__name__,
    FloorDBHandler.__name__,
    BuildingDBHandler.__name__,
    PlanDBHandler.__name__,
    UnitDBHandler.__name__,
    UserDBHandler.__name__,
    PotentialSimulationDBHandler.__name__,
    QADBHandler.__name__,
    GroupDBHandler.__name__,
    RoleDBHandler.__name__,
    FileDBHandler.__name__,
    FileCommentDBHandler.__name__,
    SlamSimulationDBHandler.__name__,
    SlamSimulationValidationDBHandler.__name__,
    UnitSimulationDBHandler.__name__,
    UnitStatsDBHandler.__name__,
    UnitAreaStatsDBHandler.__name__,
    FolderDBHandler.__name__,
    CompetitionDBHandler.__name__,
    CompetitionFeaturesDBHandler.__name__,
    CompetitionManualInputDBHandler.__name__,
    DmsPermissionDBHandler.__name__,
    ReactPlannerProjectsDBHandler.__name__,
    ManualSurroundingsDBHandler.__name__,
    ClusteringSubsamplingDBHandler.__name__,
    BulkVolumeProgressDBHandler.__name__,
    ApartmentStatsDBHandler.__name__,
)


for handler in get_db_handlers(BaseDBHandler):
    if handler == PotentialSimulationDBHandler:
        apply_retry_on_operational_errors(handler, **POTENTIAL_DB_WAIT_STRATEGY)
    else:
        apply_retry_on_operational_errors(handler)
