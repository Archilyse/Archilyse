import io
from collections import Counter
from pathlib import Path

import ezdxf
import pytest
from ezdxf import bbox
from ezdxf.entities.dxfgroups import get_group_name

from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES
from handlers import FloorHandler
from handlers.db import FloorDBHandler, UnitDBHandler
from tasks.pipeline_tasks import split_plan_task
from tests.constants import CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3
from tests.utils import assert_dxf_audit, assert_dxf_visual_differences


def test_generate_dxf_with_units(
    site,
    floor,
    plan_7641_classified,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
):
    split_plan_task(plan_id=plan_7641_classified["id"])
    UnitDBHandler.bulk_update(
        client_id={
            unit["id"]: f"apt_{i}" for i, unit in enumerate(UnitDBHandler.find())
        }
    )
    FloorDBHandler.update(
        item_pks={"id": floor["id"]},
        new_values={"plan_id": plan_7641_classified["id"]},
    )
    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"],
        language=SUPPORTED_LANGUAGES.DE,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )

    dxf_file = io.StringIO(
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs["contents"]
    )
    drawing = ezdxf.read(dxf_file)
    msp = drawing.modelspace()

    size = bbox.extents(msp).size
    # Asserts the scale factor is not too wrong
    assert (size.x, size.y) == pytest.approx((38.127, 25.624), abs=0.01)

    assert_dxf_audit(drawing=drawing)

    assert_dxf_visual_differences(
        drawing=drawing,
        expected_image_file=fixtures_path.joinpath(
            "images/dxf_images/dxf_test_floor_handler.jpeg"
        ),
    )

    actual_groups = {
        get_group_name(g, drawing.entitydb): len(g) for g in drawing.groups.groups()
    }

    assert sorted(list(actual_groups.keys())) == [
        "apt_0",
        "apt_1",
        "apt_2",
        "apt_3",
        "apt_4",
        "apt_5",
    ]
    assert sorted(actual_groups.values()) == [1, 1, 1, 1, 1, 1]

    actual_layers = Counter([e.dxf.layer for e in drawing.modelspace()])
    assert actual_layers == Counter(
        {
            "Fenster": 96,
            "Waende": 10,
            "Plankopf": 32,
            "Tueren": 50,
            "Raumstempel": 30,
            "Gelaender": 7,
            "Raumpolygone": 14,
            "SIA416-HNF": 12,
            "SIA416-ANF": 8,
            "Wohneinheiten": 6,
            "Schaechte": 4,
            "Treppen und Aufzuege": 6,
            "0": 1,
        }
    )


def test_generate_dxf_no_units(
    site,
    floor,
    plan_7641_classified,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
):
    UnitDBHandler.bulk_update(
        client_id={
            unit["id"]: f"apt_{i}" for i, unit in enumerate(UnitDBHandler.find())
        }
    )

    FloorDBHandler.update(
        item_pks={"id": floor["id"]},
        new_values={"plan_id": plan_7641_classified["id"]},
    )
    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"],
        language=SUPPORTED_LANGUAGES.DE,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )

    dxf_file = io.StringIO(
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs["contents"]
    )
    drawing = ezdxf.read(dxf_file)

    # no client IDs
    groups = {
        get_group_name(g, drawing.entitydb): len(g) for g in drawing.groups.groups()
    }
    assert not groups.keys()

    actual_layers = Counter([e.dxf.layer for e in drawing.modelspace()])
    assert actual_layers == Counter(
        {
            "Fenster": 96,
            "Waende": 10,
            "Plankopf": 32,
            "Raumstempel": 30,
            "Tueren": 38,
            "Gelaender": 7,
            "Raumpolygone": 14,
            "Schaechte": 4,
            "Treppen und Aufzuege": 6,
            "0": 1,
        }
    )

    assert_dxf_visual_differences(
        drawing=drawing,
        expected_image_file=fixtures_path.joinpath(
            "images/dxf_images/dxf_test_floor_handler_no_units.jpeg"
        ),
    )


@pytest.mark.parametrize(
    "language, expected_layers, expected_image",
    [
        (
            SUPPORTED_LANGUAGES.DE,
            {
                "Waende": 20,
                "Fenster": 56,
                "Raumstempel": 34,
                "Tueren": 80,
                "Plankopf": 32,
                "Raumpolygone": 18,
                "Gelaender": 6,
                "SIA416-HNF": 8,
                "Wohneinheiten": 4,
                "0": 1,
                "Schaechte": 8,
                "Treppen und Aufzuege": 6,
                "Sanitaer- und Kuecheneinrichtung": 38,
            },
            "test_dxf_floor_groups_de.jpeg",
        ),
        (
            SUPPORTED_LANGUAGES.FR,
            {
                "Murs": 20,
                "Fenêtres": 56,
                "Marque de zone": 34,
                "Portes": 80,
                "En-tête": 32,
                "Polygone de la pièce": 18,
                "Balustrades": 6,
                "SIA416-HNF": 8,
                "L'unité": 4,
                "0": 1,
                "Cages": 8,
                "Escaliers et Ascenseurs": 6,
                "Sanitaires et Appareils de cuisine": 38,
            },
            "test_dxf_floor_groups_fr.jpeg",
        ),
    ],
)
def test_generate_dxf_groups(
    first_pipeline_complete_db_models,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    language,
    expected_layers,
    expected_image,
):
    floor_id = first_pipeline_complete_db_models["floor"]["id"]
    FloorHandler().generate_floorplan_image(
        floor_id=floor_id,
        language=language,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )

    expected_groups = {CLIENT_ID_1: 1, CLIENT_ID_2: 1, CLIENT_ID_3: 2}

    dxf_file = io.StringIO(
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs["contents"]
    )

    drawing = ezdxf.read(dxf_file)

    assert_dxf_audit(drawing=drawing)

    assert_dxf_visual_differences(
        drawing=drawing,
        expected_image_file=fixtures_path.joinpath(
            f"images/dxf_images/{expected_image}"
        ),
    )

    actual_groups = {
        get_group_name(g, drawing.entitydb): len(g) for g in drawing.groups.groups()
    }
    actual_layers = Counter([e.dxf.layer for e in drawing.modelspace()])
    assert actual_groups == expected_groups
    assert actual_layers == expected_layers

    expected_extensions = {f".{SUPPORTED_OUTPUT_FILES.DXF.name}"}
    actual_extensions = {
        Path(call_args.kwargs["destination_file_name"]).suffix
        for call_args in mocked_gcp_upload_bytes_to_bucket.call_args_list
    }
    assert expected_extensions == actual_extensions


def test_generate_dxf_post_processed_react_data(
    floor,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    react_planner_background_image_full_plan,
    make_react_annotation_fully_pipelined,
    generate_dxf_file=False,
):
    make_react_annotation_fully_pipelined(react_planner_background_image_full_plan)
    FloorHandler().generate_floorplan_image(
        floor_id=floor["id"],
        language=SUPPORTED_LANGUAGES.DE,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )

    dxf_file = io.StringIO(
        mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs["contents"]
    )
    if generate_dxf_file:
        with Path.home().joinpath("Desktop/test_dxf_example.dxf").open("w") as f:
            f.write(dxf_file.read())
            dxf_file.seek(0)

    drawing = ezdxf.read(dxf_file)
    assert_dxf_audit(drawing=drawing)
    assert_dxf_visual_differences(
        drawing=drawing,
        expected_image_file=fixtures_path.joinpath("images/dxf_images/dxf_react.jpeg"),
    )

    actual_layers = Counter([e.dxf.layer for e in drawing.modelspace()])

    assert actual_layers == {
        "Tueren": 59,
        "Sanitaer- und Kuecheneinrichtung": 35,
        "Plankopf": 32,
        "Raumstempel": 22,
        "Fenster": 16,
        "Waende": 12,
        "Raumpolygone": 11,
        "SIA416-HNF": 20,
        "Moeblierung": 6,
        "Treppen und Aufzuege": 7,
        "Schaechte": 2,
        "Gelaender": 2,
        "Wohneinheiten": 2,
        "SIA416-FF": 2,
        "0": 1,
    }
