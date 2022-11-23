import mimetypes
from http import HTTPStatus
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from handlers.db import BuildingDBHandler, FloorDBHandler, PlanDBHandler
from ifc_reader.constants import IFC_BUILDING, IFC_SITE
from ifc_reader.reader import IfcReader
from slam_api.apis.site import add_site, site_app
from tests.flask_utils import get_address_for
from tests.utils import get_temp_path_of_extracted_file


@pytest.mark.slow
def test_import_ifc_should_merge_2_ifc_files_into_single_site_entity(
    mocker,
    fixtures_path,
    client,
    client_db,
    login,
    mocked_gcp_upload_bytes_to_bucket,
    mocked_gcp_upload_file_to_bucket,
    random_media_link,
    qa_without_site,
    site_data,
    celery_eager,
    mocked_gcp_download,
    mocked_run_generate_geo_referencing_surroundings_for_site_task,
    mocked_geolocator,
):

    from handlers.db import SiteDBHandler
    from tasks import site_ifc_tasks

    multiple_ifc_files = []
    path_side_effects = []
    building_filenames = {}
    with get_temp_path_of_extracted_file(
        fixtures_path=fixtures_path.joinpath("ifc/files"), filename="AC20-FZK-Haus"
    ) as filepath:
        reader = IfcReader(filepath=filepath)
        for i, (ref_longitude, ref_latitude) in enumerate(
            [((8, 6, 0, 0), (47, 1, 0, 0)), ((8, 8, 0, 0), (47, 3, 0, 0))]
        ):
            site = reader.wrapper.by_type(IFC_SITE)[0]
            site.RefLongitude = ref_longitude
            site.RefLatitude = ref_latitude
            site_building = reader.wrapper.by_type(IFC_BUILDING)[0]
            site_building.GlobalId = str(i)

            filename = filepath.with_name(f"test-{i}.ifc")
            reader.wrapper.write(filename.as_posix())
            path_side_effects.append(filename)
            with filename.open("rb") as f:
                fs = FileStorage(
                    stream=BytesIO(f.read()),
                    filename=f"test-{i}.ifc",
                    content_type=mimetypes.types_map[".txt"],
                )
            multiple_ifc_files.append(fs)
            building_filenames[site_building.GlobalId] = filename.name

        mocked_tmp_file = mocker.patch.object(site_ifc_tasks, "NamedTemporaryFile")
        type(
            mocked_tmp_file.return_value.__enter__.return_value
        ).name = mocker.PropertyMock(side_effect=path_side_effects)

        site_data["qa_id"] = qa_without_site["id"]
        site_data["ifc"] = multiple_ifc_files
        response = client.post(
            get_address_for(
                blueprint=site_app, use_external_address=False, view_function=add_site
            ),
            content_type="multipart/form-data",
            data=site_data,
        )
        assert response.status_code == HTTPStatus.CREATED, response.data
        site = SiteDBHandler.get_by(id=response.json["id"])
        assert pytest.approx(8.116661492918944, abs=1e-4) == site["lon"]
        assert pytest.approx(47.033334582494064, abs=1e-4) == site["lat"]

        assert all(
            p.stem == ifc_filename and ifc_link == random_media_link
            for (ifc_filename, ifc_link), p in zip(
                site["gcs_ifc_file_links"].items(), path_side_effects
            )
        )

        site_buildings = sorted(
            BuildingDBHandler.find(site_id=site["id"]), key=lambda x: x["id"]
        )
        assert len(site_buildings) == 2
        assert all(
            building["client_building_id"] == ifc_file.stem
            and building["housenumber"] == ifc_file.stem[-1]
            for (building, ifc_file) in zip(site_buildings, path_side_effects)
        )

        building_floors = list(
            FloorDBHandler.find_in(building_id=[b["id"] for b in site_buildings])
        )
        assert len(building_floors) == 4

        site_plans = PlanDBHandler.find(site_id=site["id"])
        assert len(site_plans) == 4

        number_of_uploaded_site_ifc_files = 2
        assert (
            mocked_gcp_upload_bytes_to_bucket.call_count
            + mocked_gcp_upload_file_to_bucket.call_count
            == len(site_plans) + number_of_uploaded_site_ifc_files
        )

        mocked_run_generate_geo_referencing_surroundings_for_site_task.assert_called_once_with(
            site_id=site["id"]
        )
