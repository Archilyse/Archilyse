import json
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List
from zipfile import ZipFile

import pytest
import rasterio
from shapely import wkt
from shapely.geometry import CAP_STYLE, JOIN_STYLE, MultiPolygon, Point, Polygon
from shapely.wkt import loads

from tests.utils import (
    get_temp_path_of_extracted_file,
    load_csv_as_dict,
    load_json_from_zip_file,
)

FIXTURES_PATH = Path(__file__).parent.joinpath("fixtures/")
QUAVIS_OUTPUTS_PATH = FIXTURES_PATH.joinpath("quavis_outputs")


@pytest.fixture(scope="session")
def react_planner_fixtures_path() -> Path:
    return Path(__file__).parent.parent.joinpath("ui/react-planner/src/tests/utils")


@pytest.fixture(scope="session")
def test_path() -> Path:
    return Path(__file__).parent


@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    return FIXTURES_PATH


@pytest.fixture(scope="session")
def fixtures_osm_path(fixtures_path) -> Path:
    return fixtures_path.joinpath("surroundings/osm")


@pytest.fixture(scope="session")
def fixtures_swisstopo_path(fixtures_path) -> Path:
    return fixtures_path.joinpath("surroundings/swisstopo/")


@pytest.fixture(scope="session")
def fixtures_srtm_path(fixtures_path) -> Path:
    return fixtures_path.joinpath("surroundings/srtm/")


@pytest.fixture(scope="session")
def images_path(fixtures_path) -> Path:
    return fixtures_path.joinpath("images/")


@pytest.fixture(scope="session")
def image_b_path(images_path):
    return images_path.joinpath("floorplan_b.jpg")


@pytest.fixture(scope="session")
def valid_image(images_path):
    return images_path.joinpath("image_plan_332.jpg")


@pytest.fixture(scope="session")
def pdf_floor_plan(images_path):
    return images_path.joinpath("pdf_sample.pdf")


@pytest.fixture(scope="session")
def invalid_image(images_path):
    return images_path.joinpath("not_a_valid_image.jpg")


@pytest.fixture(scope="session")
def qa_spreadsheet(fixtures_path):
    return fixtures_path.joinpath("qa_data/qa_sample.xlsx")


@pytest.fixture(autouse=True)
def mock_working_dir_temp(mocker, tmpdir):
    """This is only effective running locally"""
    from common_utils import constants

    mocker.patch.object(constants, "WORKING_DIR", Path(tmpdir))


@pytest.fixture(scope="session")
def raw_data_path(fixtures_path):
    return fixtures_path.joinpath("raw_dir")


@pytest.fixture(scope="session")
def brooks_model_json_path(raw_data_path):
    return raw_data_path.joinpath("brooks_model.json")


@pytest.fixture(scope="session")
def surroundings_sampled_path(raw_data_path):
    return raw_data_path.joinpath("2683736_1246529.csv")


@pytest.fixture(scope="session")
def unit_vector_with_balcony(fixtures_path: Path):
    with fixtures_path.joinpath("unit_vector_with_balcony.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def building_surroundings_path(fixtures_path) -> Path:
    return fixtures_path.joinpath("georeferencing/2614896.8_1268188.6.json")


@pytest.fixture
def building_footprints_as_wkts(fixtures_path) -> List[MultiPolygon]:
    from tests.fixtures.geometries.footprints_as_wkt import building_footprints_as_wkts

    return [loads(p) for p in building_footprints_as_wkts]


@pytest.fixture(scope="session")
def potential_view_results_test_api_simulations(fixtures_path: Path) -> Dict:
    with fixtures_path.joinpath(
        "potential_simulations/potential_view_results_test_api_simulations.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def potential_view_results_test_potential_view_task(fixtures_path: Path) -> Dict:
    with fixtures_path.joinpath(
        "potential_simulations/potential_view_results_test_potential_view_task.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def potential_view_results_test_potential_view_task_osm(fixtures_path: Path) -> Dict:
    with fixtures_path.joinpath(
        "potential_simulations/potential_view_results_test_potential_view_task_osm.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def invalid_layout_footprint_path(fixtures_path: Path) -> Path:
    return fixtures_path.joinpath("geometries/invalid_layout_footprint.wkt")


@pytest.fixture
def potential_sim_location() -> Point:
    return Point(2623237, 1193068)


@pytest.fixture
def swiss_building_footprint_potential(potential_sim_location) -> Polygon:
    return potential_sim_location.buffer(
        5, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
    )


@pytest.fixture
def sea_monaco_mocked(mocker, fixtures_osm_path):
    from surroundings.osm import OSMSeaHandler

    with fixtures_osm_path.joinpath("sea/monaco.shp").open(mode="r") as f:
        mocker.patch.object(OSMSeaHandler, "load_entities", return_value=json.load(f))


@pytest.fixture
def mocked_swiss_topo_building_files_and_location(
    mocker, fixtures_swisstopo_path, swiss_building_footprint_potential
) -> Polygon:
    from surroundings.swisstopo import building_surrounding_handler

    mocker.patch.object(
        building_surrounding_handler, "download_swisstopo_if_not_exists"
    )
    mocker.patch.object(
        building_surrounding_handler,
        "get_absolute_building_filepaths",
        return_value=[
            fixtures_swisstopo_path.joinpath(
                "buildings/SWISSBUILDINGS3D_2_0_CHLV95LN02_1188-11.shp"
            )
        ],
    )
    return swiss_building_footprint_potential


@pytest.fixture()
def mocked_osm_dir_fixtures(mocker, fixtures_osm_path):
    from surroundings.osm import base_osm_surrounding_handler, osm_sea_handler

    mocker.patch.object(base_osm_surrounding_handler, "OSM_DIR", fixtures_osm_path)
    mocker.patch.object(osm_sea_handler, "OSM_DIR", fixtures_osm_path)


@pytest.fixture
def mocked_osm_dir(mocker):
    import surroundings.v2.osm.geometry_provider

    with TemporaryDirectory() as temp_dir:
        mocker.patch.object(
            surroundings.v2.osm.geometry_provider, "OSM_DIR", Path(temp_dir)
        )
        return Path(temp_dir)


@pytest.fixture
def mocked_swisstopo_esri_ascii_grid(
    mocker, fixtures_swisstopo_path, mocked_gcp_download
):
    @contextmanager
    def _internal(*tiles):
        mocked_filenames = []
        with TemporaryDirectory() as temporary_directory:
            zip_dir = fixtures_swisstopo_path.joinpath("alti")
            target_dir = Path(temporary_directory).joinpath("alti")
            for tile in tiles:
                mocked_filenames.append(
                    target_dir.joinpath("esri_ascii_grid")
                    .joinpath(tile)
                    .with_suffix(".asc")
                )
                with ZipFile(
                    zip_dir.joinpath(tile).with_suffix(".zip"), "r"
                ) as zip_ref:
                    zip_ref.extractall(target_dir.joinpath("esri_ascii_grid"))

            import surroundings.utils

            mocker.patch.object(surroundings.utils, "SWISSTOPO_DIR", target_dir)

            yield mocked_filenames

    return _internal


@pytest.fixture
def mocked_srtm_tiles(
    mocker,
    fixtures_srtm_path,
    mocked_gcp_download,
):
    @contextmanager
    def _internal(*tiles):
        mocked_filenames = []
        with TemporaryDirectory() as temporary_directory:
            target_dir = Path(temporary_directory)
            for tile in tiles:
                mocked_filenames.append(target_dir.joinpath(tile).with_suffix(".tif"))
                with ZipFile(
                    fixtures_srtm_path.joinpath(tile).with_suffix(".zip"), "r"
                ) as zip_ref:
                    zip_ref.extractall(target_dir)

            import surroundings.srtm.srtm_files_handler

            mocker.patch.object(
                surroundings.srtm.srtm_files_handler, "SRTM_DIR", target_dir
            )

            yield mocked_filenames

    return _internal


@pytest.fixture
def splinter_download_dir_autoclean(splinter_file_download_dir) -> Path:
    yield Path(splinter_file_download_dir)
    for f in Path(splinter_file_download_dir).iterdir():
        f.unlink()


@pytest.fixture
def quavis_output__test_load_wrapper_from_quavis_input(fixtures_path):
    return load_json_from_zip_file(
        fixtures_path=QUAVIS_OUTPUTS_PATH,
        file_name="quavis_output_test_load_wrapper_from_quavis_input",
    )


@pytest.fixture(scope="session")
def surr_river_path(fixtures_swisstopo_path):
    return fixtures_swisstopo_path.joinpath("rivers/")


@pytest.fixture(scope="session")
def tree_surr_location(fixtures_path):
    return Point(2612953.4424275705, 1267306.2163103924)


@pytest.fixture(scope="session")
def park_surr_location(fixtures_path):
    return Point(2784998, 1152929)


@pytest.fixture(scope="session")
def ac20_fzk_haus_ifc_reader(fixtures_path):
    from ifc_reader.reader import IfcReader

    with get_temp_path_of_extracted_file(
        fixtures_path=fixtures_path.joinpath("ifc/files"), filename="AC20-FZK-Haus"
    ) as filepath:
        yield IfcReader(filepath=filepath)


@pytest.fixture(scope="session")
def ifc_file_reader_steiner_example(fixtures_path):
    from ifc_reader.reader import IfcReader

    with get_temp_path_of_extracted_file(
        fixtures_path=fixtures_path.joinpath("ifc/files"),
        filename="steiner_example",
    ) as filepath:
        yield IfcReader(filepath=filepath)


@pytest.fixture(scope="session")
def ifc_file_reader_sia_arc(fixtures_path):
    from ifc_reader.reader import IfcReader

    with get_temp_path_of_extracted_file(
        fixtures_path=fixtures_path.joinpath("ifc/files"), filename="0270_SIA_ARC"
    ) as filepath:
        yield IfcReader(filepath=filepath)


@pytest.fixture
def area_with_holes_polygon(fixtures_path):
    with fixtures_path.joinpath("geometries/area_with_holes.txt").open() as f:
        return wkt.load(f)


@pytest.fixture
def expected_room_vector_with_balcony(fixtures_path):
    with fixtures_path.joinpath("vectors/room_vector_with_balcony.json").open(
        mode="r"
    ) as f:
        return json.load(f)


@pytest.fixture
def expected_room_vector_no_balcony(fixtures_path):
    with fixtures_path.joinpath("vectors/room_vector_no_balcony.json").open(
        mode="r"
    ) as f:
        return json.load(f)


@pytest.fixture
def expected_room_vector_with_balcony_ph2022(fixtures_path):
    with open(
        fixtures_path.joinpath("vectors/room_vector_with_balcony_ph2022.json"), mode="r"
    ) as f:
        return json.load(f)


@pytest.fixture
def expected_apartment_vector_with_balcony(fixtures_path):
    with fixtures_path.joinpath("vectors/unit_vector_with_balcony.json").open("r") as f:
        return json.load(f)


@pytest.fixture
def expected_apartment_vector_no_balcony(fixtures_path):
    with fixtures_path.joinpath("vectors/unit_vector_no_balcony.json").open("r") as f:
        return json.load(f)


@pytest.fixture
def expected_full_vector_with_balcony(fixtures_path):
    with fixtures_path.joinpath("vectors/full_vector_with_balcony.json").open(
        mode="r"
    ) as f:
        return json.load(f)


@pytest.fixture
def expected_full_vector_no_balcony(fixtures_path):
    with fixtures_path.joinpath("vectors/full_vector_no_balcony.json").open(
        mode="r"
    ) as f:
        return json.load(f)


@pytest.fixture
def units_vector_fixture_for_clustering(fixtures_path):
    """
    To generate:

    from handlers import PHResultVectorHandler
    import json

    units_vector = PHResultVectorHandler(site_id=2657).generate_apartment_vector(interior_only=True)
    with open('tests/fixtures/clustering_units/units_vector_with_balcony_site_2657.json', 'w') as f:
        json.dump(units_vector, f)
    """
    with fixtures_path.joinpath(
        "clustering_units/units_vector_with_balcony_site_2657.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture
def mock_open_raster_file(fixtures_path, mocker):
    import surroundings.raster_window

    def mock_open_file(filename):
        dataset = rasterio.open(
            fixtures_path.joinpath(f"surroundings/swisstopo/noise/{filename}.tif")
        )
        mocked_call = mocker.patch.object(
            surroundings.raster_window.rasterio,
            "open",
            return_value=dataset,
        )
        return dataset, mocked_call

    return mock_open_file


@pytest.fixture
def mocked_swisstopo_dir(mocker):
    import surroundings.utils

    with TemporaryDirectory() as temp_dir:
        mocker.patch.object(surroundings.utils, "SWISSTOPO_DIR", Path(temp_dir))
        return Path(temp_dir)


@pytest.fixture
def dxf_sample(fixtures_path):
    with ZipFile(fixtures_path.joinpath("dxf/dxf_sample.dxf.zip")) as zip_file:
        return zip_file.read(name="dxf_sample.dxf")


@pytest.fixture
def dxf_sample_compliant(fixtures_path):
    with ZipFile(
        fixtures_path.joinpath("dxf/dxf_sample_compliant.dxf.zip")
    ) as zip_file:
        return zip_file.read(name="dxf_sample_compliant.dxf")


@pytest.fixture
def neufert_expected_room_vector_with_balcony(fixtures_path):
    return load_csv_as_dict(
        filepath=fixtures_path.joinpath(
            "vectors/neufert_expected_room_vector_with_balcony.csv"
        )
    )


@pytest.fixture
def neufert_expected_vector_unit_geometry(fixtures_path):
    return load_csv_as_dict(
        filepath=fixtures_path.joinpath(
            "vectors/neufert_expected_vector_unit_geometry.csv"
        )
    )
