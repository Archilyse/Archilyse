import mimetypes
import random
import tempfile
from pathlib import Path

import pytest

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    DEFAULT_RESULT_VECTORS,
    RESULT_VECTORS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    UNIT_USAGE,
)
from handlers import (
    DMSIFCDeliverableHandler,
    DMSVectorFilesHandler,
    FloorHandler,
    QAHandler,
    UnitHandler,
)
from handlers.db import ClientDBHandler, FileDBHandler, SiteDBHandler, UnitDBHandler
from handlers.ph_vector import PHResultVectorHandler
from handlers.utils import get_client_bucket_name
from tasks.utils.deliverable_utils import (
    generate_results_for_client_and_site,
    get_index_by_result_type,
)
from tests.constants import CLIENT_ID_1


@pytest.fixture
def vector_values():
    return [{"View.max.sky": 9999, "View.min.sky": 191919}]


@pytest.fixture
def janitor_unit(unit):
    return UnitDBHandler.update(
        item_pks=dict(id=unit["id"]),
        new_values=dict(
            client_id="Janitor_1",
            gcs_de_floorplan_link="random_link",
            gcs_en_floorplan_link="random_link",
            unit_usage=UNIT_USAGE.JANITOR.name,
        ),
    )


@pytest.fixture
def expected_unit_vectors(mocker, unit):

    unit_2_id = 99999999
    unit_1_values = [{"View.max.sky": 9999, "View.min.sky": 191919}]
    unit_2_values = [
        {"View.max.sky": 2.2793790292985676, "View.min.sky": 0.00037539798954355774}
    ]
    blacklisted = {"UnitBasics.area-sia416-HNF": 1, "UnitBasics.area-sia416-NNF": 2}
    unit_2_vector = [{**unit_2_values[0], **blacklisted}]

    apartment_vector_data = {
        unit["client_id"]: unit_1_values[0],
        str(unit_2_id): unit_2_vector[0],
    }
    area_vector_data = {unit["client_id"]: unit_1_values, str(unit_2_id): unit_2_vector}
    ph_result_vectors = {
        RESULT_VECTORS.UNIT_VECTOR_WITH_BALCONY: apartment_vector_data,
        RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY: area_vector_data,
        RESULT_VECTORS.FULL_VECTOR_WITH_BALCONY: apartment_vector_data,
        RESULT_VECTORS.UNIT_VECTOR_NO_BALCONY: apartment_vector_data,
        RESULT_VECTORS.ROOM_VECTOR_NO_BALCONY: area_vector_data,
        RESULT_VECTORS.FULL_VECTOR_NO_BALCONY: apartment_vector_data,
    }
    mocker.patch.object(PHResultVectorHandler, "__init__", return_value=None)
    mocker.patch.object(
        PHResultVectorHandler, "generate_vectors", return_value=ph_result_vectors
    )
    return unit_1_values, unit_2_values


@pytest.fixture
def units_with_populated_vectors(client_db, site, floor, unit):

    unit_2_id = 99999999
    apartment_no_2 = 200
    apartment_no_3 = 3
    unit_2 = UnitDBHandler.add(
        id=unit_2_id,
        site_id=unit["site_id"],
        plan_id=unit["plan_id"],
        floor_id=unit["floor_id"],
        apartment_no=apartment_no_2,
        client_id=str(unit_2_id),
    )
    unit_3 = UnitDBHandler.add(
        site_id=unit["site_id"],
        plan_id=unit["plan_id"],
        floor_id=unit["floor_id"],
        apartment_no=apartment_no_3,
        client_id=unit["client_id"],
    )
    for _unit in (unit, unit_2, unit_3):
        for language in SUPPORTED_LANGUAGES:
            for file_format in (SUPPORTED_OUTPUT_FILES.PNG, SUPPORTED_OUTPUT_FILES.PDF):
                file_name = UnitHandler().get_floorplan_image_filename(
                    unit_id=_unit["id"], language=language, file_format=file_format
                )
                FileDBHandler.add(
                    client_id=client_db["id"],
                    site_id=site["id"],
                    building_id=floor["building_id"],
                    floor_id=_unit["floor_id"],
                    unit_id=_unit["id"],
                    content_type=mimetypes.types_map[f".{file_format.name.lower()}"],
                    checksum=file_name,
                    name=file_name,
                )
    return (
        unit,
        unit_2,
        unit_3,
    )


@pytest.mark.parametrize(
    "option_dxf, option_ifc, option_analysis, upload_vectors_to_dms, option_pdf",
    [
        (False, False, True, True, True),
        (True, True, True, False, False),
        (False, False, False, False, False),
        (True, False, False, False, False),
        (True, False, True, False, True),
        (True, True, True, False, True),
    ],
)
def test_generate_client_results(
    mock_working_dir,
    mocker,
    mocked_gcp_download,
    mocked_gcp_download_file_as_bytes,
    client_db,
    site,
    plan,
    floor,
    expected_unit_vectors,
    units_with_populated_vectors,
    option_dxf,
    option_ifc,
    option_analysis,
    upload_vectors_to_dms,
    option_pdf,
):
    qa_handler_mocked = mocker.patch.object(QAHandler, "generate_qa_report")

    ClientDBHandler.update(
        item_pks=dict(id=client_db["id"]),
        new_values=dict(
            name="Portfolio Client",
            option_dxf=option_dxf,
            option_pdf=option_pdf,
            option_ifc=option_ifc,
            option_analysis=option_analysis,
        ),
    )

    mkdir_mock = mocker.patch.object(Path, "mkdir", return_value=None)
    expected_notes = "some notes"
    SiteDBHandler.update(
        item_pks=dict(id=site["id"]),
        new_values=dict(
            full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
            pipeline_and_qa_complete=True,
            validation_notes=expected_notes,
        ),
    )

    FileDBHandler.add(
        client_id=client_db["id"],
        site_id=site["id"],
        content_type=mimetypes.types_map[".zip"],
        checksum="ifc_file_checksum",
        name=DMSIFCDeliverableHandler._get_exported_ifc_file_name(site=site),
    )

    for language in SUPPORTED_LANGUAGES:
        for file_format in SUPPORTED_OUTPUT_FILES:
            FileDBHandler.add(
                client_id=client_db["id"],
                site_id=site["id"],
                building_id=floor["building_id"],
                floor_id=floor["id"],
                content_type=mimetypes.types_map[f".{file_format.name.lower()}"],
                checksum=f"floor_{file_format.name}_checksum_{language.name}",
                name=FloorHandler.get_gcs_floorplan_image_filename(
                    site_id=site["id"],
                    building_id=floor["building_id"],
                    floor_number=floor["floor_number"],
                    language=language,
                    file_format=file_format,
                ),
            )

    open_mock = mocker.patch("pathlib.Path.open", mocker.mock_open(read_data="bibble"))
    mocked_csv_writerows = mocker.patch("csv.DictWriter.writerows", autospec=True)

    if upload_vectors_to_dms and option_analysis:
        DMSVectorFilesHandler.generate_and_upload_vector_files_to_dms(
            site_id=site["id"],
            representative_units_only=False,
        )  # Tests the case where the vector files are simply downloaded from the dms

    # when
    generate_results_for_client_and_site(site=SiteDBHandler.get_by(id=site["id"]))

    # Then
    num_clients = 1
    num_sites = 1
    num_buildings = 1
    num_plans = 1
    num_raw_images = num_plans
    num_floors = 1
    num_units = 3
    num_languages = len(SUPPORTED_LANGUAGES)
    num_unit_layouts = num_units * num_languages
    num_floor_layouts = num_floors * num_languages
    num_vectors = 6

    unique_files_downloaded = {
        x.kwargs["local_file_name"] for x in mocked_gcp_download.call_args_list
    }
    unique_files_downloaded.update(
        {
            x.kwargs["source_file_name"].as_posix()
            for x in mocked_gcp_download_file_as_bytes.call_args_list
        }
    )
    client_bucket_set = {get_client_bucket_name(client_id=client_db["id"])}
    assert {
        x.kwargs["bucket_name"] for x in mocked_gcp_download.call_args_list
    } == client_bucket_set

    buckets_download_file_as_bytes = {
        x.kwargs["bucket_name"]
        for x in mocked_gcp_download_file_as_bytes.call_args_list
    }
    if len(mocked_gcp_download_file_as_bytes.call_args_list):
        assert buckets_download_file_as_bytes == client_bucket_set
    else:
        assert buckets_download_file_as_bytes == set()

    assert (
        len(unique_files_downloaded)
        == (num_floor_layouts + num_unit_layouts)
        * option_pdf
        * 2  # PNG and PDF are generated together
        + num_floor_layouts * option_dxf * 2  # DXF and DWG are generated together
        + num_raw_images
        + num_sites * option_ifc
    )

    if option_ifc:
        expected_mock_open = (num_vectors + 1) * option_analysis
    else:
        expected_mock_open = num_vectors * option_analysis
    expected_mock_open += (
        num_floor_layouts * option_dxf * 2
        + (num_floor_layouts + num_unit_layouts) * option_pdf * 2
    )
    assert open_mock.call_count == expected_mock_open

    assert (
        mkdir_mock.call_count
        == num_clients
        + num_sites
        + num_buildings
        + num_floors
        * (
            1
            + option_pdf * 2  # PNG and PDF are downloaded together
            + option_dxf * 2  # DXF and DWG are generated together
            + option_analysis
        )  # +1 for the raw images. Floor level
        + num_buildings * num_units * option_pdf * 2  # Unit level folder
        + num_sites * option_ifc
        + 1  # qa report
    )

    assert qa_handler_mocked.call_count == 1  # qa report is always generated

    assert (
        mocked_csv_writerows.call_count
        == len(DEFAULT_RESULT_VECTORS) * num_sites * option_analysis
    )
    unit, unit_2, unit_3 = units_with_populated_vectors
    unit_1_values, unit_2_values = expected_unit_vectors
    for row in mocked_csv_writerows.call_args_list:
        #  Results are ordered by floor number and apartment no as secondary.
        #  All units are in the same floor. Last unit to be aggregated by client_id remainsaaaa
        assert row[0][1] == [
            {
                "apartment_no": unit_3["apartment_no"],
                "floor_number": floor["floor_number"],
                "client_id": CLIENT_ID_1,
                **unit_1_values[0],
            },
            {
                "apartment_no": unit_2["apartment_no"],
                "floor_number": floor["floor_number"],
                "client_id": unit_2["client_id"],
                **unit_2_values[0],
            },
        ]


def test_get_index_by_result_type_excludes_janitor_units(
    client_db, site, janitor_unit, mocker
):
    # assumes site sim version stays at PH_2021
    mocker.patch.object(
        PHResultVectorHandler,
        PHResultVectorHandler.generate_vectors.__name__,
        return_value={
            RESULT_VECTORS.UNIT_VECTOR_WITH_BALCONY: {
                janitor_unit["client_id"]: {"foobar"}
            }
        },
    )

    assert get_index_by_result_type(
        site_id=site["id"], representative_units_only=False
    ) == {
        vector.value: []
        for vector in [
            RESULT_VECTORS.UNIT_VECTOR_WITH_BALCONY,
            RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY,
            RESULT_VECTORS.FULL_VECTOR_WITH_BALCONY,
            RESULT_VECTORS.UNIT_VECTOR_NO_BALCONY,
            RESULT_VECTORS.ROOM_VECTOR_NO_BALCONY,
            RESULT_VECTORS.FULL_VECTOR_NO_BALCONY,
        ]
    }


def test_download_vector_files_excludes_janitor_units(
    client_db, site, janitor_unit, plan, floor, vector_values, mocker
):
    # assumes site sim version stays at PH_2021
    unit_2_client_id = str(random.randint(0, 255))
    mocker.patch.object(PHResultVectorHandler, "__init__", return_value=None)
    mocker.patch.object(
        PHResultVectorHandler,
        "generate_vectors",
        return_value={
            RESULT_VECTORS.UNIT_VECTOR_WITH_BALCONY: {
                janitor_unit["client_id"]: {"foobar"},
                unit_2_client_id: vector_values[0],
            },
            RESULT_VECTORS.UNIT_VECTOR_NO_BALCONY: {
                janitor_unit["client_id"]: {"foobar"},
                unit_2_client_id: vector_values[0],
            },
            RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY: {
                janitor_unit["client_id"]: [{"foobar"}],
                unit_2_client_id: vector_values,
            },
            RESULT_VECTORS.ROOM_VECTOR_NO_BALCONY: {
                janitor_unit["client_id"]: [{"foobar"}],
                unit_2_client_id: vector_values,
            },
            RESULT_VECTORS.FULL_VECTOR_WITH_BALCONY: {
                janitor_unit["client_id"]: {"foobar"},
                unit_2_client_id: vector_values[0],
            },
            RESULT_VECTORS.FULL_VECTOR_NO_BALCONY: {
                janitor_unit["client_id"]: {"foobar"},
                unit_2_client_id: vector_values[0],
            },
        },
    )
    ClientDBHandler.update(
        item_pks=dict(id=client_db["id"]),
        new_values=dict(name="Good Life", option_analysis=True),
    )
    # Unit that WILL have results
    UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=janitor_unit["apartment_no"] + 1,
        client_id=unit_2_client_id,
        gcs_de_floorplan_link="random_link",
        gcs_en_floorplan_link="random_link",
    )

    with tempfile.TemporaryDirectory() as tmpdirname:
        DMSVectorFilesHandler.download_vector_files(
            site_id=site["id"], download_path=Path(tmpdirname)
        )

        for file in Path(tmpdirname).iterdir():
            with file.open("r") as csv_file:
                num_lines = len([x for x in csv_file])
                # header + rows per unit that are not janitor
                assert num_lines == 2
