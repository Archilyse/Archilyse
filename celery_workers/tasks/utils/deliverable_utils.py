from pathlib import Path
from typing import Dict, List, Optional

from brooks.types import SIACategory
from common_utils.constants import (
    OUTPUT_DIR,
    RESULT_VECTORS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    UNIT_USAGE,
)
from common_utils.logger import logger
from handlers import (
    DMSFloorDeliverableHandler,
    DMSIFCDeliverableHandler,
    DMSUnitDeliverableHandler,
    DMSVectorFilesHandler,
    GCloudStorageHandler,
    QAHandler,
    UnitHandler,
)
from handlers.constants import GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE
from handlers.db import (
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_client_bucket_name

BLACKLISTED_FIELDS = [
    f"UnitBasics.area-sia416-{category.name}" for category in SIACategory
]
BLACKLISTED_FIELDS += [
    "area_index",
    "Sun.v2.max.sun-2018-12-21 08:00:00+01:00",
    "Sun.v2.mean.sun-2018-12-21 08:00:00+01:00",
    "Sun.v2.min.sun-2018-12-21 08:00:00+01:00",
    "Sun.v2.std.sun-2018-12-21 08:00:00+01:00",
]

gcloud = GCloudStorageHandler()


def client_site_id(site: Dict) -> str:
    """Get Client site ID"""
    return str(site["client_site_id"] or site["id"]).replace("/", "-")


def _building_address(building: Dict) -> str:
    """ """
    if building["street"]:
        return f'{building["street"]}-{building["housenumber"]}'.replace("/", "-")
    return building["housenumber"].replace("/", "-")


def _create_path(base_path: Path, postfix: str) -> Path:
    """Check and create a path"""
    new_path = base_path.joinpath(postfix)
    new_path.mkdir(exist_ok=True, parents=True)
    return new_path


def unit_is_representative(unit, representative_units_only: bool):
    if representative_units_only:
        return unit["client_id"] == unit["representative_unit_client_id"]
    return True


def get_index_by_result_type(
    site_id: int, representative_units_only: bool
) -> Dict[str, List[Dict]]:
    """Fetch units and subunits data"""
    from handlers.ph_vector import PHResultVectorHandler

    ph_vector_handler = PHResultVectorHandler(site_id=site_id)

    index: Dict[str, List[Dict]] = {}
    # We want to have empty headers at least
    for vector_type in ph_vector_handler.RELEVANT_RESULT_VECTORS:
        index[vector_type.value] = []

    apartment_vectors = ph_vector_handler.generate_vectors()
    floors_index = {x["id"]: x for x in FloorDBHandler.find_by_site_id(site_id=site_id)}

    units_in_db = sorted(
        UnitDBHandler.find(site_id=site_id), key=lambda x: x["apartment_no"]
    )
    units_aggregated = {
        unit["client_id"]: unit
        for unit in units_in_db
        if (
            unit["unit_usage"] == UNIT_USAGE.RESIDENTIAL.name
            and unit_is_representative(
                unit=unit, representative_units_only=representative_units_only
            )
        )
    }

    logger.info(
        f"Removed {len(units_in_db) - len(units_aggregated)} duplicates, "
        f"theoretically maisonettes and non-representative units, "
        f"from a total of {len(units_in_db)} units. Remaining: {len(units_aggregated)}"
    )

    for client_unit_id, unit in units_aggregated.items():
        additional_fields = {
            "apartment_no": unit["apartment_no"],
            "floor_number": floors_index[unit["floor_id"]]["floor_number"],
            "client_id": unit["client_id"],
        }
        for vector_type in ph_vector_handler.RELEVANT_RESULT_VECTORS:
            apartment_vector = apartment_vectors[vector_type].get(client_unit_id)
            if apartment_vector is None:
                raise Exception(
                    f"Can't find result name `{vector_type.value}` for unit `{client_unit_id}`"
                    f" and site `{site_id}`."
                )
            if vector_type in [
                RESULT_VECTORS.ROOM_VECTOR_NO_BALCONY,
                RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY,
            ]:
                for area_vector in apartment_vector:
                    area_vector.update(additional_fields)
                    index[vector_type.value].append(area_vector)
            else:
                apartment_vector.update(additional_fields)
                index[vector_type.value].append(apartment_vector)

    return index


def _download_floors_content(
    building: Dict, site: Dict, building_path: Path, client: Dict
):
    """
    Folder structure:
    |---> Layouts
        |---> {floor_number}
            |---> floor_{floor_number}_floorplan_{language.name}.png
            |---> Units
                |---> {client_site_id}_floorplan_{language.name}.png

    """

    # Get by floors
    for floor in FloorDBHandler.find(building_id=building["id"]):
        floor_prefix = f"floor_{floor['floor_number']}"

        units_in_floor = UnitDBHandler.get_joined_by_site_building_floor_id(
            site_id=site["id"], building_id=building["id"], floor_id=floor["id"]
        )
        # Fetch PNGs
        if client["option_pdf"]:
            for file_format in (SUPPORTED_OUTPUT_FILES.PDF, SUPPORTED_OUTPUT_FILES.PNG):
                layouts_path = _create_path(base_path=building_path, postfix="Layouts")
                download_floor_pngs(
                    floor=floor,
                    floor_prefix=floor_prefix,
                    layouts_path=layouts_path,
                    file_format=file_format,
                )
                download_unit_pngs(
                    client_id=client["id"],
                    floor=floor,
                    units_in_floor=units_in_floor,
                    layouts_path=layouts_path,
                    file_format=file_format,
                )

        # Fetch DXF files
        if client["option_dxf"]:
            for file_format in (SUPPORTED_OUTPUT_FILES.DWG, SUPPORTED_OUTPUT_FILES.DXF):
                download_floor_dxf_dwg(
                    path=_create_path(
                        base_path=building_path, postfix=file_format.name
                    ),
                    floor=floor,
                    file_format=file_format,
                )


def download_unit_pngs(
    client_id: int,
    units_in_floor: List[dict],
    floor: dict,
    layouts_path: Path,
    file_format: SUPPORTED_OUTPUT_FILES,
):
    for unit in units_in_floor:
        unit_layouts_path = _create_path(base_path=layouts_path, postfix="units")
        for language in SUPPORTED_LANGUAGES:
            file_content = DMSUnitDeliverableHandler.download_unit_file(
                client_id=client_id,
                unit_id=unit["id"],
                language=language,
                file_format=file_format,
            )
            file_path = unit_layouts_path.joinpath(
                UnitHandler.unique_image_filename(
                    unit_info=unit,
                    floor_info=floor,
                    language=language,
                    file_format=file_format,
                )
            )
            with file_path.open("wb") as f:
                f.write(file_content)


def download_floor_dxf_dwg(
    path: Path, floor: dict, file_format: SUPPORTED_OUTPUT_FILES
):
    for language in SUPPORTED_LANGUAGES:
        file_content: bytes = DMSFloorDeliverableHandler.download_floor_file(
            floor_id=floor["id"], language=language, file_format=file_format
        )
        with path.joinpath(
            f"floor_{floor['floor_number']}_{language.name}_plot"
            f".{DMSUnitDeliverableHandler.suffix_normalization(extension=file_format.name)}"
        ).open("wb") as f:
            f.write(file_content)


def download_floor_pngs(
    floor: dict,
    floor_prefix: str,
    layouts_path: Path,
    file_format: SUPPORTED_OUTPUT_FILES,
):
    for language in SUPPORTED_LANGUAGES:
        file_content = DMSFloorDeliverableHandler.download_floor_file(
            floor_id=floor["id"], file_format=file_format, language=language
        )
        with layouts_path.joinpath(
            f"{floor_prefix}_floorplan_{language.name}"
            f".{DMSUnitDeliverableHandler.suffix_normalization(extension=file_format.name)}"
        ).open("wb") as f:
            f.write(file_content)


def _download_ifc(site: dict, ifc_path: Path):
    for language, _ in GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[
        SUPPORTED_OUTPUT_FILES.IFC
    ].items():
        file_content: bytes = DMSIFCDeliverableHandler.download_ifc_file(
            site_id=site["id"]
        )
        with ifc_path.joinpath(f"{site['client_site_id']}_{language.name}.zip").open(
            "wb"
        ) as f:
            f.write(file_content)


def _download_raw_images(building: Dict, building_path: Path, client_id: int):
    """Get raw images by floor"""
    raw_path = _create_path(base_path=building_path, postfix="Raw images")
    for plan in PlanDBHandler.find(building_id=building["id"]):
        for floor in FloorDBHandler.find(plan_id=plan["id"]):
            ext = plan["image_mime_type"].split("/")[-1]
            gcloud.download_file_from_media_link(
                bucket_name=get_client_bucket_name(client_id=client_id),
                source_media_link=plan["image_gcs_link"],
                destination_file=raw_path.joinpath(f'{floor["floor_number"]}.{ext}'),
            )


def generate_results_for_client_and_site(site: Dict, output_dir: Optional[str] = None):
    """Generate result folder for a client and a site

    Folder structure:
    Client folder (e.g. Portfolio Client)
    |---> Site as client_site_id (e.g. 1234)
        |---> Vectors
            |---> {client_site_id}-{filename}.csv
        |---> Street building (e.g. somestreet 13)
            |---> Layouts
                |---> {floor_number}
                    |---> floor_{floor_number}_floorplan_{language.name}.png
                    |---> Units
                        |---> {client_site_id}_floorplan_{language.name}.png
            |---> Raw images
                |---> {floor_number}.jpeg
            |--> DXF
                |--> floor_{floor_number}-plot.dxf
        |--> IFC
            |--> {client_site_id}_{language.name}.ifc
        |--> QA_REPORT
            |--> {client_site_id}_qa_report.csv
    """
    client = ClientDBHandler.get_by(id=site["client_id"])
    client_path = _create_path(
        base_path=Path(output_dir or OUTPUT_DIR), postfix=client["name"]
    )
    site_path = _create_path(base_path=client_path, postfix=client_site_id(site))
    if client["option_analysis"]:
        # Vectors
        DMSVectorFilesHandler.download_vector_files(
            site_id=site["id"],
            download_path=_create_path(
                base_path=site_path, postfix=DMSVectorFilesHandler.FOLDERNAME
            ),
        )

    # Buildings
    for building in BuildingDBHandler.find(site_id=site["id"]):
        building_path = _create_path(
            base_path=site_path, postfix=_building_address(building)
        )
        _download_floors_content(
            building=building, site=site, building_path=building_path, client=client
        )
        _download_raw_images(
            building=building, building_path=building_path, client_id=client["id"]
        )

    if client["option_ifc"]:
        ifc_path = _create_path(base_path=site_path, postfix="IFC")
        _download_ifc(site=site, ifc_path=ifc_path)

    # QA report
    qa_path = _create_path(base_path=site_path, postfix="QA_REPORT")
    QAHandler(site_id=site["id"]).generate_qa_report().to_csv(
        qa_path.joinpath(f"{site['client_site_id']}_qa_report.csv")
    )

    for path in client_path.rglob("*.checksum"):
        path.unlink()
