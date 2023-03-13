import copy
from pathlib import Path

import click
from pandas import DataFrame, ExcelWriter

from common_utils.constants import UNIT_USAGE
from common_utils.logger import logger
from handlers.db import (
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from handlers.energy_reference_area.energy_calculation_per_layout import (
    EnergyAreaStatsLayout,
)
from handlers.energy_reference_area.models import (
    DetailedAreaInformation,
    EnergyAreasStatsPerFloor,
)


class EnergyAreaReportForSite:
    @classmethod
    def create_report(cls, site_id: int, outputpath: Path = None):
        outputpath = outputpath or Path().cwd().joinpath(
            f"energy_area_report_site_{site_id}.xlsx"
        )
        data_per_floor = cls._data_per_floor(site_id=site_id)

        with ExcelWriter(outputpath) as writer:

            cls._prepare_data_per_building(data_per_floor=data_per_floor).to_excel(
                excel_writer=writer, sheet_name="Per Building"
            )
            cls._prepare_data_per_floor(data_per_floor=data_per_floor).to_excel(
                excel_writer=writer, sheet_name="Per Floor", index=False
            )
            cls._prepare_data_per_area(data_per_floor=data_per_floor).to_excel(
                excel_writer=writer, sheet_name="Detailed Area Information", index=False
            )

    @classmethod
    def _data_per_floor(cls, site_id: int) -> list[EnergyAreasStatsPerFloor]:
        from handlers import PlanLayoutHandler

        data_per_floor = []
        for building in BuildingDBHandler.find(
            site_id=site_id, output_columns=["id", "client_building_id"]
        ):
            plan_id_energy_area_stats = {
                plan["id"]: EnergyAreaStatsLayout.energy_area_in_layout(
                    layout=PlanLayoutHandler(plan_id=plan["id"]).get_layout(
                        scaled=True, classified=True
                    ),
                    area_ids_part_of_units=cls._area_ids_part_of_units(site_id=site_id),
                )
                for plan in PlanDBHandler.find(
                    building_id=building["id"], output_columns=["id"]
                )
            }
            for floor in FloorDBHandler.find(
                building_id=building["id"], output_columns=["plan_id", "floor_number"]
            ):
                floor_stats: EnergyAreasStatsPerFloor = copy.deepcopy(
                    plan_id_energy_area_stats[floor["plan_id"]]
                )
                floor_stats.floor_number = floor["floor_number"]
                floor_stats.building_client_id = building["client_building_id"]
                data_per_floor.append(floor_stats)

        return data_per_floor

    @classmethod
    def _area_ids_part_of_units(cls, site_id: int) -> set[int]:
        return {
            unit_area["area_id"]
            for unit_area in UnitAreaDBHandler.find_in(
                unit_id=[
                    unit["id"]
                    for unit in UnitDBHandler.find_in(
                        site_id={site_id},
                        unit_usage={UNIT_USAGE.RESIDENTIAL, UNIT_USAGE.COMMERCIAL},
                        output_columns={"id"},
                    )
                ],
                output_columns=["area_id"],
            )
        }

    @classmethod
    def _prepare_data_per_building(
        cls,
        data_per_floor: list[EnergyAreasStatsPerFloor],
    ) -> DataFrame:
        df = DataFrame(data_per_floor)
        df = df[
            [
                "total_era_volume",
                "total_non_era_area",
                "era_wall_area",
                "building_client_id",
            ]
        ]
        return df.groupby(df["building_client_id"]).aggregate(
            {
                "total_era_volume": "sum",
                "total_non_era_area": "sum",
                "era_wall_area": "sum",
            }
        )

    @classmethod
    def _prepare_data_per_floor(
        cls,
        data_per_floor: list[EnergyAreasStatsPerFloor],
    ) -> DataFrame:
        column_order_and_filter = [
            "building_client_id",
            "floor_number",
            "total_era_area",
            "total_non_era_area",
            "era_wall_area",
        ]
        return DataFrame(data_per_floor)[column_order_and_filter]

    @classmethod
    def _prepare_data_per_area(
        cls,
        data_per_floor: list[EnergyAreasStatsPerFloor],
    ) -> DataFrame:
        area_informations = []
        for floor_data in data_per_floor:
            for area_type, area_sizes in floor_data.era_areas.items():
                for area_size in area_sizes:
                    area_informations.append(
                        DetailedAreaInformation(
                            area_type=area_type,
                            area_size=area_size,
                            era_area=area_size,
                            era_volume=area_size * floor_data.floor_height,
                            floor_number=floor_data.floor_number,
                            building_client_id=floor_data.building_client_id,
                        )
                    )
            for area_type, area_sizes in floor_data.non_era_areas.items():
                for area_size in area_sizes:
                    area_informations.append(
                        DetailedAreaInformation(
                            area_type=area_type,
                            area_size=area_size,
                            era_area=0,
                            era_volume=0,
                            floor_number=floor_data.floor_number,
                            building_client_id=floor_data.building_client_id,
                        )
                    )
            for area_type, area_sizes in floor_data.era_areas_volume_only.items():
                for area_size in area_sizes:
                    area_informations.append(
                        DetailedAreaInformation(
                            area_type=area_type,
                            area_size=area_size,
                            era_area=0,
                            era_volume=area_size * floor_data.floor_height,
                            floor_number=floor_data.floor_number,
                            building_client_id=floor_data.building_client_id,
                        )
                    )
        column_order = [
            "building_client_id",
            "floor_number",
            "area_type",
            "area_size",
            "era_area",
            "era_volume",
        ]
        return DataFrame(data=area_informations)[column_order]


@click.command()
@click.option("--site_id", "-s", prompt=True, type=click.INT)
def era_report(site_id: int):

    report_path = Path().cwd().joinpath(f"era_report_site_{site_id}.xlsx")
    EnergyAreaReportForSite.create_report(site_id=site_id, outputpath=report_path)

    logger.info(f"Saved at {report_path}")


if __name__ == "__main__":
    era_report()
