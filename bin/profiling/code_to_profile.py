import timeit

from common_utils.constants import TASK_TYPE
from common_utils.logger import logger
from handlers import SlamSimulationHandler


def code_to_profile():
    SlamSimulationHandler.get_simulation_results_formatted(
        unit_id=146025, simulation_type=TASK_TYPE.NOISE, georeferenced=True
    )


num_of_executions = 10
logger.info(
    f"time it takes to run {num_of_executions} "
    f"times: {timeit.timeit(lambda: code_to_profile(), number=num_of_executions)}s"
)
