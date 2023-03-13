from pathlib import Path
from tempfile import NamedTemporaryFile

from deepdiff import DeepDiff
from pandas import read_excel

from brooks.types import AreaType
from handlers.energy_reference_area.main_report import EnergyAreaReportForSite


def test_generate_energy_reference_report(site_with_3_units):
    with NamedTemporaryFile(suffix=".xlsx") as f:
        EnergyAreaReportForSite.create_report(
            site_id=site_with_3_units["site"]["id"], outputpath=Path(f.name)
        )
        df_per_building = read_excel(f.name, sheet_name="Per Building")
        assert not DeepDiff(
            df_per_building.to_dict(),
            {
                "building_client_id": {0: 1},
                "total_era_volume": {0: 1071.59858891194},
                "total_non_era_area": {0: 4.354330312503265},
                "era_wall_area": {0: 81.61682319673241},
            },
            ignore_order=True,
            significant_digits=3,
        )
        df_per_floor = read_excel(f.name, sheet_name="Per Floor")
        assert not DeepDiff(
            df_per_floor.to_dict(),
            {
                "building_client_id": {0: 1},
                "floor_number": {0: 1},
                "total_era_area": {0: 412.1533034276692},
                "total_non_era_area": {0: 4.354330312503265},
                "era_wall_area": {0: 81.61682319673241},
            },
            ignore_order=True,
            significant_digits=3,
        )

        df_per_areas = read_excel(f.name, sheet_name="Detailed Area Information")

        assert (
            sum(
                [
                    elem
                    for elem in df_per_areas.loc[
                        df_per_areas["area_type"] == AreaType.STOREROOM.name
                    ]["era_area"]
                ]
            )
            > 0
        )  # Asserts that storerooms are counted as energy reference area as they are part of residential unit
        assert df_per_areas.to_dict().keys() == {
            "area_type",
            "area_size",
            "era_area",
            "era_volume",
            "floor_number",
            "building_client_id",
        }
