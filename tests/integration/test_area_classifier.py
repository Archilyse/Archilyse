import tempfile
from pathlib import Path

import pytest

from brooks.area_classifier import AreaClassifier
from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.exceptions import (
    InaccurateClassifierException,
    NotEnoughTrainingDataClassifierException,
)
from handlers.db import PlanDBHandler, SiteDBHandler


@pytest.mark.skip
def test_train_area_classifier(
    mocked_plan_image_upload_to_gc,
    make_plans,
    make_classified_plans,
    site,
    building,
):
    plan_fixture_ids = dict(
        [
            (
                2494,
                1.85518929777984e-05,
            ),
            (
                5797,
                0.000747469144362779,
            ),
            (
                5825,
                0.000725269861441508,
            ),
            (
                6951,
                7.33718054410552e-05,
            ),
        ],
    )
    plans = make_plans(*[building for _ in plan_fixture_ids])
    for plan, (fixture_plan_id, georef_scale) in zip(plans, plan_fixture_ids.items()):
        make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={
                "annotation_finished": True,
                "georef_scale": georef_scale,
                "georef_x": 0.0,
                "georef_y": 0.0,
                "georef_rot_angle": 0.0,
                "georef_rot_x": 0,
                "georef_rot_y": 0,
            },
        )

    SiteDBHandler.update(
        item_pks=dict(id=site["id"]),
        new_values=dict(full_slam_results=ADMIN_SIM_STATUS.SUCCESS),
    )
    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir).joinpath("classifier.pickle")
    classifier = AreaClassifier()

    with pytest.raises(NotEnoughTrainingDataClassifierException):
        classifier.train(output_path=output_path, min_required_plans=5, n_jobs=1)

    with pytest.raises(InaccurateClassifierException):
        classifier.train(
            output_path=output_path,
            min_required_plans=3,
            min_model_accuracy=1,
            n_jobs=1,
        )

    classifier.train(
        output_path=output_path, min_required_plans=3, min_model_accuracy=0, n_jobs=1
    )
    assert output_path.exists()
