from common_utils.constants import VIEW_DIMENSION
from handlers.sim_validators.base_validator import BaseValidator

SUN_DIMENSION_JUNE_MIDDAY = "sun_june_midday"


class UnitsHighSiteViewValidator(BaseValidator):
    msg = "Too high site view. Does it have windows?"

    HIGH_SITE_VIEW_THRESHOLD = 12.5

    def eval_condition(
        self,
        unit_id: int,
    ) -> bool:
        return (
            self.units_stats[unit_id][VIEW_DIMENSION.VIEW_SITE.value]["min"]
            > self.HIGH_SITE_VIEW_THRESHOLD
        )


class UnitsLowSunValidator(BaseValidator):
    msg = "Too low sun. Does it have windows?"

    LOW_SUN_THRESHOLD = 0.1

    def eval_condition(
        self,
        unit_id: int,
    ) -> bool:
        return (
            self.units_stats[unit_id][SUN_DIMENSION_JUNE_MIDDAY]["max"]
            < self.LOW_SUN_THRESHOLD
        )
