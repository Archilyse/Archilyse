import io
import mimetypes
import zipfile
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

from brooks.models import SimLayout
from brooks.unit_layout_factory import UnitLayoutFactory
from brooks.visualization.brooks_plotter import BrooksPlotter
from common_utils.constants import (
    GOOGLE_CLOUD_CLOUD_CONVERT_FILES,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
)
from common_utils.exceptions import DBNotFoundException
from handlers import (
    ClientHandler,
    DMSFloorDeliverableHandler,
    DMSIFCDeliverableHandler,
    DMSUnitDeliverableHandler,
    DMSVectorFilesHandler,
    FileHandler,
    FloorHandler,
    PlanLayoutHandler,
    UnitHandler,
)
from handlers.db import FileDBHandler, FolderDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.ifc import IfcExportHandler
from handlers.utils import get_client_bucket_name

test_file_name = "test file to ignore"


@pytest.fixture
def dms_files_uploaded(site, client_db, make_sites):
    """To make sure we handle correctly the queries we create the same files in different sites"""
    (site_b,) = make_sites(client_db)
    files = []
    site_a = site
    for site in (site_a, site_b):
        files.extend(
            [
                FileDBHandler.add(
                    name=test_file_name,
                    checksum="checksum1",
                    site_id=site["id"],
                    client_id=site["client_id"],
                    content_type="something fake",
                ),
                FileDBHandler.add(
                    name=DMSIFCDeliverableHandler._get_exported_ifc_file_name(
                        site=site
                    ),
                    checksum="checksum_ifc",
                    site_id=site["id"],
                    client_id=site["client_id"],
                    content_type="something fake",
                ),
            ]
        )

    return files


class TestDMSDeliverableHandlerIFC:
    @staticmethod
    def test_ifc_export_upload(
        site,
        floor,
        plan,
        gereferenced_annotation_for_plan_5797,
        random_media_link,
        mocker,
        mocked_gcp_upload_bytes_to_bucket,
        make_areas_from_layout,
    ):
        from handlers.dms import dms_deliverable_handler

        make_areas_from_layout(
            layout=PlanLayoutHandler(plan_id=plan["id"]).get_layout(
                raise_on_inconsistency=False
            ),
            plan_id=plan["id"],
        )

        mocked_tmp_file = mocker.patch.object(
            dms_deliverable_handler, "NamedTemporaryFile"
        )
        with NamedTemporaryFile() as f:
            local_file_name = f.name
        type(
            mocked_tmp_file.return_value.__enter__.return_value
        ).name = mocker.PropertyMock(return_value=local_file_name)

        ifc_exporter_spy = mocker.spy(IfcExportHandler, "__init__")
        DMSIFCDeliverableHandler.generate_ifc_and_upload_to_dms(site_id=site["id"])

        assert ifc_exporter_spy.call_args_list[0].kwargs["site_id"] == site["id"]

        upload_kwargs = mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs
        upload_kwargs.pop("contents")
        checksum = upload_kwargs.pop("destination_file_name")
        # checksum changes every time

        assert upload_kwargs == {
            "destination_folder": Path("dms"),
            "content_type": mimetypes.types_map[".zip"],
            "bucket_name": get_client_bucket_name(client_id=site["client_id"]),
        }

        with zipfile.ZipFile(
            file=Path(local_file_name).with_suffix(".zip")
        ) as ifc_zipped_file:
            assert ifc_zipped_file.namelist() == ["Bigassportfolio.ifc"]

        files = FileDBHandler.find()
        assert len(files) == 1
        file = files[0]
        file.pop("created")
        file.pop("id")
        assert 45000 > file.pop("size") > 30000  # it has minor changes -> flaky
        assert file == {
            "area_id": None,
            "building_id": None,
            "checksum": checksum,
            "client_id": site["client_id"],
            "comments": [],
            "content_type": mimetypes.types_map[".zip"],
            "creator_id": None,
            "deleted": False,
            "floor_id": None,
            "folder_id": None,
            "labels": DMSIFCDeliverableHandler.default_ifc_tags,
            "name": f"{site['client_site_id']} - Exported IFC en.zip",
            "site_id": site["id"],
            "unit_id": None,
            "updated": None,
        }

    @staticmethod
    def test_dms_ifc_download(mocker, site, dms_files_uploaded):
        mocked_download = mocker.patch.object(FileHandler, "download")
        DMSIFCDeliverableHandler.download_ifc_file(site_id=site["id"])
        mocked_download.assert_called_once_with(
            client_id=site["client_id"], checksum="checksum_ifc"
        )

    @staticmethod
    def test_dms_replace_non_existing_file(mocker, site):
        remove_mocked = mocker.patch.object(FileHandler, "remove")
        create_mocked = mocker.patch.object(FileHandler, "create")
        DMSIFCDeliverableHandler.create_or_replace_dms_file(
            client_id=site["client_id"],
            site_id=site["id"],
            extension=".zip",
            labels=[],
            filename=test_file_name,
            buff=io.StringIO("123123"),
        )
        assert create_mocked.call_count == 1
        assert remove_mocked.call_count == 0

    @staticmethod
    def test_dms_replace_existing_file(mocker, site, dms_files_uploaded):
        remove_mocked = mocker.patch.object(FileHandler, "remove")
        create_mocked = mocker.patch.object(FileHandler, "create")
        DMSIFCDeliverableHandler.create_or_replace_dms_file(
            client_id=site["client_id"],
            site_id=site["id"],
            extension=".zip",
            labels=[],
            filename=test_file_name,
            buff=io.StringIO("123123"),
        )
        assert create_mocked.call_count == 1
        remove_mocked.assert_called_once_with(file_id=dms_files_uploaded[0]["id"])


class TestDMSDeliverableHandlerFloor:
    @staticmethod
    def test_generate_upload_floorplan(
        mocker, mocked_gcp_upload_bytes_to_bucket, floor, site
    ):
        text_content = "text file like a dxf"
        file_name = "file.dxf"
        mocker.patch.object(
            FloorHandler,
            "generate_floorplan_image",
            return_value=(
                StringIO(text_content),
                file_name,
                {"client_id": site["client_id"], "id": site["id"]},
            ),
        )

        DMSFloorDeliverableHandler().generate_upload_floorplan(
            floor_id=floor["id"],
            language=SUPPORTED_LANGUAGES.EN,
            file_format=SUPPORTED_OUTPUT_FILES.DXF,
        )

        upload_kwargs = mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs
        upload_kwargs.pop("contents")

        assert upload_kwargs == {
            "destination_folder": Path("dms"),
            "content_type": mimetypes.types_map[".dxf"],
            "destination_file_name": "cs6iGRQO3LGGBu%2FdTPdOKA%3D%3D",
            "bucket_name": get_client_bucket_name(client_id=site["client_id"]),
        }

        files = FileDBHandler.find()
        assert len(files) == 1
        file = files[0]
        file.pop("created")
        file.pop("id")
        assert file.pop("size") == len(text_content)
        assert file == {
            "area_id": None,
            "building_id": None,
            "checksum": "cs6iGRQO3LGGBu%2FdTPdOKA%3D%3D",
            "client_id": site["client_id"],
            "comments": [],
            "content_type": mimetypes.types_map[".dxf"],
            "creator_id": None,
            "deleted": False,
            "floor_id": floor["id"],
            "folder_id": None,
            "labels": ["DXF"],
            "name": file_name,
            "site_id": site["id"],
            "unit_id": None,
            "updated": None,
        }

    @staticmethod
    def test_convert_and_upload_dwg(
        mocker,
        site,
        floor,
        mocked_gcp_download_file_as_bytes,
        mocked_gcp_upload_bytes_to_bucket,
        mocked_gcp_delete,
        celery_eager,
    ):
        from handlers import CloudConvertHandler, cloud_convert

        # Given
        dxf_image_filename = FloorHandler.get_gcs_floorplan_image_filename(
            site_id=site["id"],
            building_id=floor["building_id"],
            floor_number=floor["floor_number"],
            language=SUPPORTED_LANGUAGES.EN,
            file_format=SUPPORTED_OUTPUT_FILES.DXF,
        )
        FileDBHandler.add(
            name=dxf_image_filename,
            checksum="checksum1",
            site_id=site["id"],
            floor_id=floor["id"],
            client_id=site["client_id"],
            content_type="something fake",
        )
        fake_media_link = "fake_media_link"
        mocker.patch.object(FileHandler, "get_media_link", return_value=fake_media_link)
        mocked_import_task = mocker.patch.object(
            CloudConvertHandler,
            "import_from_file",
        )
        mocked_convert_task = mocker.patch.object(
            CloudConvertHandler,
            "convert",
        )
        mocked_export_task = mocker.patch.object(CloudConvertHandler, "export_to_file")
        # When
        mocked_tmp_file = mocker.patch.object(cloud_convert, "NamedTemporaryFile")
        with NamedTemporaryFile() as f:
            local_file_name = f.name
            type(
                mocked_tmp_file.return_value.__enter__.return_value
            ).name = mocker.PropertyMock(return_value=local_file_name)

            mocked_tmp_file.return_value.__enter__.return_value.read.return_value = (
                b"dwg_content_dummy"
            )

            DMSFloorDeliverableHandler.convert_and_upload_dwg(
                floor_id=floor["id"], language=SUPPORTED_LANGUAGES.EN
            )

        # Then
        expected_bucket = get_client_bucket_name(client_id=site["client_id"])
        mocked_import_task.assert_called_with(source_file_path=Path(local_file_name))
        mocked_convert_task.assert_called_with(
            input_format=SUPPORTED_OUTPUT_FILES.DXF.name.lower(),
            output_format=SUPPORTED_OUTPUT_FILES.DWG.name.lower(),
        )
        dwg_file_name = (
            Path(dxf_image_filename)
            .with_suffix(f".{SUPPORTED_OUTPUT_FILES.DWG.name.lower()}")
            .name
        )
        mocked_export_task.assert_called_with(
            destination_file_path=Path(local_file_name)
        )

        mocked_gcp_delete.assert_called_with(
            bucket_name=expected_bucket,
            source_folder=GOOGLE_CLOUD_CLOUD_CONVERT_FILES,
            filename=Path(dwg_file_name),
        )

        assert (
            mocked_gcp_upload_bytes_to_bucket.call_args.kwargs["contents"]
            == b"dwg_content_dummy"
        )

        dms_dwg_file = FileDBHandler.get_by(name=dwg_file_name, floor_id=floor["id"])
        assert dms_dwg_file["labels"] == ["DWG"]

    @staticmethod
    def test_download_floor_file_with_dwg_extension(
        mocker,
        client_db,
        floor,
        mocked_gcp_download_file_as_bytes,
        mocked_gcp_upload_bytes_to_bucket,
        mocked_gcp_delete,
        celery_eager,
    ):
        get_filename_spy = mocker.spy(FloorHandler, "get_gcs_floorplan_image_filename")
        file_db_handler_mock = mocker.patch.object(
            FileDBHandler,
            "get_by",
            return_value={"client_id": client_db["id"], "checksum": "1234"},
        )
        DMSFloorDeliverableHandler.download_floor_file(
            floor_id=floor["id"],
            language=SUPPORTED_LANGUAGES.EN,
            file_format=SUPPORTED_OUTPUT_FILES.DWG,
        )
        filename = get_filename_spy.spy_return
        assert Path(filename).suffix == ".dwg"
        mocked_gcp_download_file_as_bytes.assert_called_once()
        file_db_handler_mock.assert_called_once_with(
            floor_id=floor["id"], name=filename, client_id=client_db["id"]
        )


class TestDMSDeliverableHandlerUnit:
    @staticmethod
    def test_generate_upload_floorplan(
        mocker, mocked_gcp_upload_bytes_to_bucket, unit, site
    ):
        text_content = b"text file like a png image"
        file_name = "file.png"
        mocker.patch.object(
            UnitHandler,
            "generate_floorplan_image",
            return_value=(
                io.BytesIO(text_content),
                file_name,
                {"client_id": site["client_id"], "id": site["id"]},
            ),
        )

        DMSUnitDeliverableHandler().generate_upload_floorplan(
            unit_id=unit["id"],
            language=SUPPORTED_LANGUAGES.EN,
            file_format=SUPPORTED_OUTPUT_FILES.PNG,
        )

        upload_kwargs = mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs
        upload_kwargs.pop("contents")

        assert upload_kwargs == {
            "destination_folder": Path("dms"),
            "content_type": "image/png",
            "destination_file_name": "dQpc1WBxRBQEsnLKUFB7kg%3D%3D",
            "bucket_name": get_client_bucket_name(client_id=site["client_id"]),
        }

        files = FileDBHandler.find()
        assert len(files) == 1
        file = files[0]
        file.pop("created")
        file.pop("id")
        assert file.pop("size") == len(text_content)
        assert file == {
            "area_id": None,
            "building_id": None,
            "checksum": "dQpc1WBxRBQEsnLKUFB7kg%3D%3D",
            "client_id": site["client_id"],
            "comments": [],
            "content_type": "image/png",
            "creator_id": None,
            "deleted": False,
            "floor_id": None,
            "unit_id": unit["id"],
            "folder_id": None,
            "labels": ["PNG"],
            "name": file_name,
            "site_id": site["id"],
            "updated": None,
        }


class TestDMSVectorFilesHandler:
    def test_upload_and_download_vector_files_to_from_dms(
        self, site, mocked_gcp_upload_bytes_to_bucket, mocker
    ):
        # UPLOAD
        mocker.patch(
            "tasks.utils.deliverable_utils.get_index_by_result_type", return_value=None
        )
        mocker.patch.object(
            DMSVectorFilesHandler, "_get_unit_vectors", return_value=[{"key": "value"}]
        )
        DMSVectorFilesHandler.generate_and_upload_vector_files_to_dms(
            site_id=site["id"],
            representative_units_only=False,
        )

        assert mocked_gcp_upload_bytes_to_bucket.call_count == 6
        assert {
            call_arg.kwargs["content_type"]
            for call_arg in mocked_gcp_upload_bytes_to_bucket.call_args_list
        } == {"text/csv"}

        db_folders = FolderDBHandler.find()
        assert len(db_folders) == 1
        assert db_folders[0]["name"] == "Vectors"
        assert db_folders[0]["client_id"] == site["client_id"]
        assert db_folders[0]["site_id"] == site["id"]

        db_files = FileDBHandler.find()
        assert len(db_files) == 6
        assert {db_file["name"] for db_file in db_files} == {
            "Leszku-payaso-room_vector_with_balcony.csv",
            "Leszku-payaso-full_vector_no_balcony.csv",
            "Leszku-payaso-unit_vector_no_balcony.csv",
            "Leszku-payaso-unit_vector_with_balcony.csv",
            "Leszku-payaso-room_vector_no_balcony.csv",
            "Leszku-payaso-full_vector_with_balcony.csv",
        }
        for db_file in db_files:
            assert db_file["client_id"] == site["client_id"]
            assert db_file["site_id"] == site["id"]
            assert db_file["folder_id"] == db_folders[0]["id"]

        # DOWNLOAD
        mocker.patch.object(FileHandler, "download", return_value=b"some_binary")
        spy_vector_files_generation = mocker.spy(
            DMSVectorFilesHandler, "_generate_vector_files"
        )
        with TemporaryDirectory() as fout:
            DMSVectorFilesHandler.download_vector_files(
                site_id=site["id"],
                download_path=Path(fout),
            )
            downloaded_files = [path for path in Path(fout).iterdir()]
            assert (
                spy_vector_files_generation.call_count == 0
            )  # if files already exist in dms they shouldn't be created again
            assert len(downloaded_files) == 6
            assert {file.name for file in downloaded_files} == {
                "Leszku-payaso-room_vector_no_balcony.csv",
                "Leszku-payaso-full_vector_with_balcony.csv",
                "Leszku-payaso-room_vector_with_balcony.csv",
                "Leszku-payaso-unit_vector_no_balcony.csv",
                "Leszku-payaso-unit_vector_with_balcony.csv",
                "Leszku-payaso-full_vector_no_balcony.csv",
            }

    def test_generate_and_download_files_if_not_exist_in_dms(self, site, mocker):
        mocker.patch(
            "tasks.utils.deliverable_utils.get_index_by_result_type", return_value=None
        )
        mocker.patch.object(
            DMSVectorFilesHandler, "_get_unit_vectors", return_value=[{"key": "value"}]
        )
        mocker.patch.object(FileHandler, "download", return_value=b"some_binary")
        spy_vector_files_generation = mocker.spy(
            DMSVectorFilesHandler, "_generate_vector_files"
        )
        with TemporaryDirectory() as fout:
            DMSVectorFilesHandler.download_vector_files(
                site_id=site["id"],
                download_path=Path(fout),
            )
            downloaded_files = [path for path in Path(fout).iterdir()]
            assert spy_vector_files_generation.call_count == 1
            assert len(downloaded_files) == 6
            assert {file.name for file in downloaded_files} == {
                "Leszku-payaso-room_vector_no_balcony.csv",
                "Leszku-payaso-full_vector_with_balcony.csv",
                "Leszku-payaso-room_vector_with_balcony.csv",
                "Leszku-payaso-unit_vector_no_balcony.csv",
                "Leszku-payaso-unit_vector_with_balcony.csv",
                "Leszku-payaso-full_vector_no_balcony.csv",
            }

    def test_generate_vector_files_if_no_units_present(
        self, mocker, site, plan, basic_features_finished
    ):
        mocker.patch.object(
            DMSVectorFilesHandler, "_get_existing_dms_folder", return_value=None
        )
        with TemporaryDirectory() as fout:
            with pytest.raises(
                DBNotFoundException,
                match=f"No simulation found for site {site['id']} and task type VIEW_SUN",
            ):
                DMSVectorFilesHandler.download_vector_files(
                    site_id=site["id"], download_path=fout
                )

    def test_files_and_folders_are_replaced_by_reupload(
        self, site, mocker, mocked_gcp_upload_bytes_to_bucket, mocked_gcp_delete
    ):
        # UPLOAD
        mocker.patch(
            "tasks.utils.deliverable_utils.get_index_by_result_type", return_value=None
        )
        mocker.patch.object(
            DMSVectorFilesHandler, "_get_unit_vectors", return_value=[{"key": "value"}]
        )
        DMSVectorFilesHandler.generate_and_upload_vector_files_to_dms(
            site_id=site["id"],
            representative_units_only=False,
        )
        files_ids_first_upload = {file["id"] for file in FileDBHandler.find()}
        folder_ids_first_upload = {folder["id"] for folder in FolderDBHandler.find()}

        # REUPLOAD
        DMSVectorFilesHandler.generate_and_upload_vector_files_to_dms(
            site_id=site["id"],
            representative_units_only=False,
        )

        files_ids_second_upload = {file["id"] for file in FileDBHandler.find()}
        folder_ids_second_upload = {folder["id"] for folder in FolderDBHandler.find()}

        assert (
            mocked_gcp_upload_bytes_to_bucket.call_count == 2 * 6
        )  # 2 uploads times 6 vector files
        assert mocked_gcp_delete.call_count == 6
        assert len(files_ids_second_upload) == 6
        assert len(folder_ids_second_upload) == 1
        assert not files_ids_first_upload.intersection(files_ids_second_upload)
        assert not folder_ids_first_upload.intersection(folder_ids_second_upload)


def test_floor_generate_upload_floorplan_caches_layouts(
    mocker,
    mocked_gcp_upload_bytes_to_bucket,
    plan_georeferenced,
    floor,
    make_units,
    make_annotations,
):
    make_annotations(plan_georeferenced)
    make_units(floor, floor)
    mocker.patch.object(DMSFloorDeliverableHandler, "create_or_replace_dms_file")
    # mocks inside floor handler in order
    mocker.patch.object(ClientHandler, "get_logo_content", return_value=b"asdsadas")
    mocked_mapper_get_layout_raw = mocker.patch.object(
        ReactPlannerToBrooksMapper, "get_layout", return_value=SimLayout()
    )
    mocker.patch.object(BrooksPlotter, "generate_floor_plot")
    mocker.patch.object(
        UnitLayoutFactory, "create_sub_layout", return_value=SimLayout()
    )
    # When
    handler = DMSFloorDeliverableHandler()
    handler.generate_upload_floorplan(
        floor_id=1,
        language=SUPPORTED_LANGUAGES.EN,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )
    handler.generate_upload_floorplan(
        floor_id=1,
        language=SUPPORTED_LANGUAGES.DE,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )
    # Then
    assert mocked_mapper_get_layout_raw.call_count == 1
