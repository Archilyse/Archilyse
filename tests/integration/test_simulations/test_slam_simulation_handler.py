from common_utils.constants import SIMULATION_VERSION, TASK_TYPE
from handlers import SlamSimulationHandler
from handlers.db import SiteDBHandler


def test_get_simulation_results_formatted(mocker, unit, site):
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"simulation_version": SIMULATION_VERSION.PH_2022_H1.value},
    )
    sim_view_ph_2022 = {
        unit["id"]: {
            "bla": [10, 10],
            "isovist": [6.109950065612793, 6.125125885009766],
            "highways": [2, 2],
            "pedestrians": [0.004821681417524815, 0.006485717371106148],
            "primary_streets": [1, 1],
            "tertiary_streets": [0.0012753034243360162, 0.0017316725570708513],
            "secondary_streets": [0, 0],
            "observation_points": [
                [1246043.192029937, 2704511.861984874, 684.61611160952],
                [1246043.1785281883, 2704512.111620013, 684.61611160952],
            ],
        }
    }
    mocker.patch.object(
        SlamSimulationHandler,
        SlamSimulationHandler.get_results.__name__,
        return_value=sim_view_ph_2022,
    )
    result = SlamSimulationHandler.get_simulation_results_formatted(
        project=False,
        georeferenced=True,
        simulation_type=TASK_TYPE.VIEW_SUN,
        unit_id=unit["id"],
    )
    assert "streets" in result.keys()
    assert len(result["streets"]) == 2
    assert result["streets"] == [3.006096984841861, 3.008217389928177]
