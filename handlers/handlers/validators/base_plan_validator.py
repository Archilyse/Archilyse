from functools import cached_property
from typing import List, Union

from brooks.classifications import UnifiedClassificationScheme
from brooks.models.violation import SpatialEntityViolation, Violation


class BasePlanValidator:
    def __init__(self, plan_id: int) -> None:
        self.plan_id = plan_id

    @cached_property
    def classification_scheme(self) -> UnifiedClassificationScheme:
        return UnifiedClassificationScheme()

    def validate(
        self,
    ) -> Union[List[Violation], List[SpatialEntityViolation]]:
        """
        Interface method for validating areas passed to the view function, in order to create an apartment (unit).
        """
        raise NotImplementedError()

    @staticmethod
    def get_human_id(
        plan_id: int,
        apartment_no: int,
    ) -> str:
        return f"Plan id: {plan_id}, apartment_no: {apartment_no}"
