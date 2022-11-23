import pytest
import shapely
from shapely.geometry import Point

from common_utils.constants import SWISSTOPO_BUILDING_FILES_PREFIX


def test_get_required_swisstopo_filepaths(mock_working_dir):
    from surroundings.utils import (
        get_required_swisstopo_filepaths,
        get_surroundings_bounding_box,
    )

    lv95_location = Point(2614896.8, 1268188.6)
    bounding_box = get_surroundings_bounding_box(lv95_location.x, lv95_location.y)

    relative_required_swisstopo_filepaths = get_required_swisstopo_filepaths(
        bounding_box
    )

    expected_required_files = {
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/MISSING_LAKES/Brienzersee.wkt",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/MISSING_LAKES/Vierwaldstätter See.wkt",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_AREALE/swissTLM3D_TLM_FREIZEITAREAL.shp",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_EINZELBAUM_GEBUESCH.shp",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.shp",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.shp",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_OEV/swissTLM3D_TLM_EISENBAHN.shp",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_STRASSEN/swissTLM3D_TLM_STRASSE.shp",
        "esri_ascii_grid/swiss_1047_4.asc",
        SWISSTOPO_BUILDING_FILES_PREFIX + "SWISSBUILDINGS3D_2_0_CHLV95LN02_1047-43.shp",
    }

    assert not expected_required_files.difference(relative_required_swisstopo_filepaths)


def test_get_required_filepaths_ignores_out_of_grid_exception(mocker):
    import surroundings.utils
    from common_utils.constants import SWISSTOPO_REQUIRED_FILES_BUILDINGS
    from common_utils.exceptions import OutOfGridException
    from surroundings.utils import (
        get_required_swisstopo_filepaths,
        get_surroundings_bounding_box,
    )

    mocker.patch.object(
        surroundings.utils, "lv95_to_lk25_subindex", side_effect=OutOfGridException()
    )

    location_within_grid = 1173000.0, 2825625.0

    assert (
        get_required_swisstopo_filepaths(
            bounding_box=get_surroundings_bounding_box(
                *location_within_grid, bounding_box_extension=100
            ),
            templates=SWISSTOPO_REQUIRED_FILES_BUILDINGS,
        )
        == set()
    )


def test_get_required_filepaths_ignore_missing(mock_working_dir):
    from common_utils.constants import SWISSTOPO_REQUIRED_FILES_BUILDINGS
    from surroundings.utils import (
        get_required_swisstopo_filepaths,
        get_surroundings_bounding_box,
    )

    north, east = 1173000.0, 2825625.0

    lv95_location = Point(east + 10, north + 10)
    bounding_box = get_surroundings_bounding_box(
        x=lv95_location.x, y=lv95_location.y, bounding_box_extension=10
    )

    relative_required_swisstopo_filepaths = get_required_swisstopo_filepaths(
        bounding_box=bounding_box, templates=SWISSTOPO_REQUIRED_FILES_BUILDINGS
    )
    assert not relative_required_swisstopo_filepaths


def test_download_surroundings_if_not_exist(mock_working_dir, mocked_gcp_download):
    from surroundings.utils import (
        download_swisstopo_if_not_exists,
        get_surroundings_bounding_box,
    )

    lv95_location = Point(2614896.8, 1268188.6)
    bounding_box = get_surroundings_bounding_box(lv95_location.x, lv95_location.y)
    download_swisstopo_if_not_exists(bounding_box)

    assert mocked_gcp_download.call_count == 36


@pytest.fixture
def layout_footprint():
    return shapely.wkt.loads(
        "MULTIPOLYGON (((2678942.756940573 1289656.104638894, 2678942.87179 "
        "1289656.04888, 2678938.623490001 1289647.369199998, 2678931.77521 "
        "1289650.621460001, 2678931.808144381 1289650.731170139, 2678930.482119999 "
        "1289651.374119998, 2678934.60877 1289660.060539998, 2678942.756940573 "
        "1289656.104638894)))"
    )
