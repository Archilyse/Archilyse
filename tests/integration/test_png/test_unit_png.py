import io
import json
from pathlib import Path

import pytest
from PIL import Image

from common_utils.constants import (
    GOOGLE_CLOUD_RESULT_IMAGES,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
)
from handlers import ClientHandler, SlamSimulationHandler, UnitHandler
from handlers.constants import GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE
from handlers.db import AreaDBHandler, PlanDBHandler, UnitAreaDBHandler, UnitDBHandler
from handlers.utils import get_client_bucket_name
from tasks.pipeline_tasks import split_plan_task
from tests.constants import CLIENT_ID_1, UNIT_ID_1
from tests.utils import assert_image_phash


@pytest.mark.parametrize(
    "fixture_plan_id, georef_scale, rot_angle, expected_image_path, language",
    [
        (
            4976,
            0.000074,
            312.854498274469,
            "images/unit_pngs/2207171-01-01-0001-floorplan-splited-floorplan-and-splitters_IT.png",
            SUPPORTED_LANGUAGES.IT,
        ),
        (
            3489,
            0.00028,
            335.284253385872,
            "images/unit_pngs/03-0303-floorplan_large_separators_case.png",
            SUPPORTED_LANGUAGES.DE,
        ),
        (
            4976,
            0.000074,
            312.854498274469,
            "images/unit_pngs/2207171-01-01-0001-floorplan-splited-floorplan-and-splitters_DE.png",
            SUPPORTED_LANGUAGES.DE,
        ),
        (
            7641,
            7.12961037842059e-05,
            78.8484917824914,
            "images/unit_pngs/7641_unit.png",
            SUPPORTED_LANGUAGES.DE,
        ),
    ],
)
@pytest.mark.parametrize(
    "file_format", [SUPPORTED_OUTPUT_FILES.PNG, SUPPORTED_OUTPUT_FILES.PDF]
)
def test_generate_unit_floorplan(
    site,
    plan,
    floor,
    result_vector_paths,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    make_classified_plans,
    fixture_plan_id,
    georef_scale,
    rot_angle,
    expected_image_path,
    basic_features_finished,
    mocker,
    language,
    file_format,
):
    make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
    areas = AreaDBHandler.find(plan_id=plan["id"])
    split_plan_task(plan_id=plan["id"])

    # Select the unit we want to plot
    areas_sorted = sorted(areas, key=lambda x: sum((x["coord_x"], x["coord_y"])))
    index = -1
    if fixture_plan_id == 4976:
        index = 0
    selected_area = areas_sorted[index]

    unit_id = UnitAreaDBHandler.get_by(area_id=selected_area["id"])["unit_id"]
    UnitDBHandler.update(
        item_pks={"id": unit_id}, new_values={"client_id": CLIENT_ID_1}
    )

    vector_path = result_vector_paths[UNIT_ID_1]["full_vector_with_balcony"]
    with vector_path.open() as fh:
        result_vector = json.load(fh)
    SlamSimulationHandler.store_results(
        run_id=basic_features_finished["run_id"],
        results={unit_id: [result_vector]},
    )

    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values={
            "georef_rot_angle": rot_angle,
            "georef_scale": georef_scale,
            "georef_rot_x": 0,
            "georef_rot_y": 0,
        },
    )

    with fixtures_path.joinpath("images/myclient_logo.png").open("rb") as f:
        mocker.patch.object(ClientHandler, "get_logo_content", return_value=f.read())

    UnitHandler().generate_floorplan_image(
        unit_id=unit_id, language=language, file_format=file_format
    )
    unit_info = UnitDBHandler.get_by(id=unit_id)
    expected_file_name_in_gcs = UnitHandler().get_floorplan_image_filename(
        unit_id=unit_id, language=language, file_format=file_format
    )

    assert mocked_gcp_upload_bytes_to_bucket.call_count == 1
    assert (
        unit_info[GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][language]]
        is not None
    )

    assert mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs[
        "bucket_name"
    ] == get_client_bucket_name(client_id=site["client_id"])
    assert (
        Path(
            mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs[
                "destination_folder"
            ]
        )
        == GOOGLE_CLOUD_RESULT_IMAGES
    )
    assert (
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs[
            "destination_file_name"
        ]
        == expected_file_name_in_gcs
    )

    if file_format == SUPPORTED_OUTPUT_FILES.PNG:
        new_file = io.BytesIO(
            mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs["contents"]
        )
        with Image.open(new_file) as new_image_content:
            assert_image_phash(
                expected_image_file=fixtures_path.joinpath(expected_image_path),
                new_image_content=new_image_content,
            )
