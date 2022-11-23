import io
from pathlib import Path

import pytest
from matplotlib import pyplot
from matplotlib.backends import backend_agg, backend_pdf
from PIL import Image

from brooks.visualization.floorplans.layouts.floor_layout import AssetManagerFloorLayout
from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES
from handlers import ClientHandler, FloorHandler
from handlers.constants import GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE
from handlers.db import FloorDBHandler, PlanDBHandler
from tasks.pipeline_tasks import split_plan_task
from tests.utils import assert_image_phash


def test_generate_full_floorplan_react(
    floor,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    react_planner_background_image_full_plan,
    make_react_annotation_fully_pipelined,
):
    react_plan_extended_fully_pipelined = make_react_annotation_fully_pipelined(
        react_planner_background_image_full_plan
    )
    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"],
        language=SUPPORTED_LANGUAGES.DE,
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )

    assert_image_no_visual_differences_regression(
        expected_image_file=fixtures_path.joinpath(
            "images/floor_pngs/react-full-floorplan_DE.png"
        ),
        mocked_gcp_upload_bytes_to_bucket=mocked_gcp_upload_bytes_to_bucket,
        plan=react_plan_extended_fully_pipelined["plan"],
        floor=floor,
        language=SUPPORTED_LANGUAGES.DE,
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )


def test_generate_axis_floor(
    make_classified_plans,
    mocker,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    site,
    plan,
    building,
    floor,
):
    fixture_plan_id = 3489
    language = SUPPORTED_LANGUAGES.DE
    georef_data = {
        "georef_scale": 0.00028,
        "georef_rot_x": 0,
        "georef_rot_y": 0,
        "georef_rot_angle": 335.284253385872,
    }
    make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
    PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=georef_data)
    dummy_fig, dummy_ax = pyplot.subplots()

    mocker.patch.object(
        AssetManagerFloorLayout, "axis_orientation", return_value=dummy_ax
    )
    mocker.patch.object(AssetManagerFloorLayout, "axis_metadata", return_value=dummy_ax)
    mocker.patch.object(AssetManagerFloorLayout, "axis_logo", return_value=dummy_ax)
    mocker.patch.object(
        AssetManagerFloorLayout, "axis_legal_advise", return_value=dummy_ax
    )
    mocker.patch.object(
        AssetManagerFloorLayout, "axis_scale", return_value=(dummy_ax, 1)
    )
    mocker.patch.object(
        AssetManagerFloorLayout, "axis_separator", return_value=dummy_ax
    )

    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"], language=language, file_format=SUPPORTED_OUTPUT_FILES.PNG
    )

    assert_image_no_visual_differences_regression(
        expected_image_file=fixtures_path.joinpath(
            "images/floor_pngs/3489-floor-axis-DE.png"
        ),
        mocked_gcp_upload_bytes_to_bucket=mocked_gcp_upload_bytes_to_bucket,
        plan=plan,
        floor=floor,
        language=language,
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )


def assert_image_no_visual_differences_regression(
    expected_image_file,
    mocked_gcp_upload_bytes_to_bucket,
    plan,
    floor,
    language,
    file_format,
):
    image_filename = FloorHandler.get_gcs_floorplan_image_filename(
        site_id=plan["site_id"],
        building_id=floor["building_id"],
        floor_number=floor["floor_number"],
        language=language,
        file_format=file_format,
    )
    assert (
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs[
            "destination_file_name"
        ]
        == image_filename
    )
    new_file = io.BytesIO(
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs["contents"]
    )
    with Image.open(new_file) as new_image_content:
        assert_image_phash(
            expected_image_file=expected_image_file,
            new_image_content=new_image_content,
        )


@pytest.mark.parametrize(
    "language, fixture_plan_id, georef_data, expected",
    [
        (
            SUPPORTED_LANGUAGES.FR,
            5825,
            {
                "georef_scale": 0.000725269861441508,
                "georef_rot_x": 619.908070026149,
                "georef_rot_y": -377.449287221441,
                "georef_rot_angle": 219.115103841475,
            },
            "5825-full_floorplan_FR.png",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            5825,
            {
                "georef_scale": 0.000725269861441508,
                "georef_rot_x": 619.908070026149,
                "georef_rot_y": -377.449287221441,
                "georef_rot_angle": 219.115103841475,
            },
            "5825-full_floorplan_DE.png",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            5797,
            {
                "georef_scale": 0.000747469144362779,
                "georef_rot_x": 397.5,
                "georef_rot_y": -297,
                "georef_rot_angle": 291.941460997825,
            },
            "5797-full_floorplan_DE.png",
        ),
        (
            SUPPORTED_LANGUAGES.EN,
            5797,
            {
                "georef_scale": 0.000747469144362779,
                "georef_rot_x": 397.5,
                "georef_rot_y": -297,
                "georef_rot_angle": 291.941460997825,
            },
            "5797-full_floorplan_EN.png",
        ),
        (
            SUPPORTED_LANGUAGES.DE,
            7641,
            {
                "georef_rot_angle": 78.8484917824914,
                "georef_rot_x": 2383.69635750003,
                "georef_rot_y": -1057.29354085503,
                "georef_scale": 7.12961037842059e-05,
            },
            "7641-full_floorplan_DE.png",
        ),
    ],
)
@pytest.mark.parametrize(
    "file_format", [SUPPORTED_OUTPUT_FILES.PNG, SUPPORTED_OUTPUT_FILES.PDF]
)
def test_generate_full_floorplan(
    make_classified_plans,
    mocker,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    site,
    plan,
    building,
    floor,
    language,
    fixture_plan_id,
    georef_data,
    expected,
    file_format,
):
    make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
    PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=georef_data)

    # To create also the units so that we can validate the entrance door feature, the plan 7641
    # should be split into 3 apartments on each side of the floor, but it only creates 2, totalling 4
    split_plan_task(plan_id=plan["id"])

    png_renderer_spy = mocker.spy(backend_agg, "RendererAgg")
    pdf_renderer_spy = mocker.spy(backend_pdf, "RendererPdf")

    with fixtures_path.joinpath("images/myclient_logo.png").open("rb") as f:
        mocker.patch.object(ClientHandler, "get_logo_content", return_value=f.read())

    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"], language=language, file_format=file_format
    )

    expected_image_file = fixtures_path.joinpath(f"images/floor_pngs/{expected}")
    if file_format == SUPPORTED_OUTPUT_FILES.PNG:
        assert_image_no_visual_differences_regression(
            expected_image_file=expected_image_file,
            mocked_gcp_upload_bytes_to_bucket=mocked_gcp_upload_bytes_to_bucket,
            plan=plan,
            floor=floor,
            language=language,
            file_format=file_format,
        )

    for supported_language in SUPPORTED_LANGUAGES:
        link = FloorDBHandler.get_by(id=floor["id"])[
            GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][supported_language]
        ]
        if supported_language == language:
            assert link is not None
        else:
            assert link is None

    # Check that it's stored as png and that the savefig command is executed accordingly
    expected_extensions = {f".{file_format.name}"}
    actual_extensions = {
        Path(call_args.kwargs["destination_file_name"]).suffix
        for call_args in mocked_gcp_upload_bytes_to_bucket.call_args_list
    }
    expected_file_name = FloorHandler.get_gcs_floorplan_image_filename(
        site_id=site["id"],
        building_id=building["id"],
        floor_number=floor["floor_number"],
        language=language,
        file_format=file_format,
    )
    assert (
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs[
            "destination_file_name"
        ]
        == expected_file_name
    )
    assert expected_extensions == actual_extensions

    # Assert that the correct renderers have been called
    if file_format == SUPPORTED_OUTPUT_FILES.PNG:
        png_renderer_spy.assert_called_once()
    elif file_format == SUPPORTED_OUTPUT_FILES.PDF:
        pdf_renderer_spy.assert_called_once()


@pytest.mark.parametrize(
    "language, fixture_plan_id, georef_data, expected",
    [
        (
            SUPPORTED_LANGUAGES.FR,
            5825,
            {
                "georef_scale": 0.000725269861441508,
                "georef_rot_x": 619.908070026149,
                "georef_rot_y": -377.449287221441,
                "georef_rot_angle": 219.115103841475,
            },
            "5825-full_floorplan_no_units.png",
        ),
    ],
)
def test_generate_full_floorplan_png_no_units(
    make_classified_plans,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    site,
    plan,
    building,
    floor,
    language,
    fixture_plan_id,
    georef_data,
    expected,
):
    make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
    PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=georef_data)

    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"], language=language, file_format=SUPPORTED_OUTPUT_FILES.PNG
    )
    expected_image_file = fixtures_path.joinpath(f"images/floor_pngs/{expected}")
    assert_image_no_visual_differences_regression(
        expected_image_file=expected_image_file,
        mocked_gcp_upload_bytes_to_bucket=mocked_gcp_upload_bytes_to_bucket,
        plan=plan,
        floor=floor,
        language=language,
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )
