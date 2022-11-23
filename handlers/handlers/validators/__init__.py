from handlers.validators.unit_areas.unit_area_validation import (
    AllAreasSpacesSelectedValidator,
    AreasNotDefinedValidator,
    DoorValidator,
    ForeignPlanAreaValidator,
    SpacesConnectedValidator,
    SpacesDoorsSinglePolygonValidator,
    SpacesUnionSinglePolygonValidator,
    UnitAccessibleValidator,
    UnitAreaValidator,
    UnitKitchenCountValidator,
)

from .classification import PlanClassificationValidator
from .classification.balcony_has_railings import (
    PlanClassificationBalconyHasRailingValidator,
)
from .classification.door_number_validator import PlanClassificationDoorNumberValidator
from .classification.feature_consistency_validator import (
    PlanClassificationFeatureConsistencyValidator,
)
from .classification.room_window_validator import PlanClassificationRoomWindowValidator
from .classification.shaft_validator import PlanClassificationShaftValidator
from .georeferencing.plan_overlap_validator import PlanOverlapValidator
from .linking.unit_linking_validator import UnitLinkingValidator
from .qa_georeferencing import GeoreferencingValidator

__all__ = (
    UnitAreaValidator.__name__,
    AllAreasSpacesSelectedValidator.__name__,
    ForeignPlanAreaValidator.__name__,
    AreasNotDefinedValidator.__name__,
    UnitAccessibleValidator.__name__,
    SpacesConnectedValidator.__name__,
    SpacesDoorsSinglePolygonValidator.__name__,
    SpacesUnionSinglePolygonValidator.__name__,
    GeoreferencingValidator.__name__,
    DoorValidator.__name__,
    UnitKitchenCountValidator.__name__,
    PlanClassificationDoorNumberValidator.__name__,
    PlanClassificationShaftValidator.__name__,
    PlanClassificationFeatureConsistencyValidator.__name__,
    PlanClassificationRoomWindowValidator.__name__,
    PlanClassificationBalconyHasRailingValidator.__name__,
    PlanOverlapValidator.__name__,
    PlanClassificationValidator.__name__,
    UnitLinkingValidator.__name__,
)
