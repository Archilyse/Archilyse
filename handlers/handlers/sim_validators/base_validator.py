import abc
from typing import Dict


class BaseValidator(abc.ABC):
    @property
    @abc.abstractmethod
    def msg(self) -> str:
        pass

    def __init__(self, units_stats):
        self.units_stats = units_stats

    def validate(self) -> Dict[int, str]:
        violation_list = {}
        for unit_id in self.units_stats.keys():
            if self.eval_condition(unit_id=unit_id):
                violation_list[unit_id] = self.msg
        return violation_list

    @abc.abstractmethod
    def eval_condition(self, unit_id: int) -> bool:
        pass
