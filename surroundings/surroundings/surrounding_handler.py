import csv
from itertools import chain
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Iterator, Optional
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from contexttimer import timer
from shapely.geometry import CAP_STYLE, JOIN_STYLE, MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

from common_utils.chunker import chunker
from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_VIEW_SURROUNDINGS,
    REGION,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
    SURROUNDINGS_DIR,
    SurroundingType,
)
from common_utils.logger import logger
from handlers import GCloudStorageHandler
from surroundings.base_elevation_handler import (
    BaseElevationHandler,
    get_elevation_handler,
)
from surroundings.constants import (
    BOUNDING_BOX_EXTENSION_GROUNDS,
    BOUNDING_BOX_EXTENSION_SAMPLE,
)
from surroundings.manual_surroundings import (
    ManualBuildingSurroundingHandler,
    ManualExclusionSurroundingHandler,
)
from surroundings.osm import (
    OSMBuildingsHandler,
    OSMForestHandler,
    OSMGroundsHandler,
    OSMLakesHandler,
    OSMParksHandler,
    OSMRailwayHandler,
    OSMRiversHandler,
    OSMSeaHandler,
    OSMStreetHandler,
    OSMTreesHandler,
)
from surroundings.osm.osm_grounds_handler import FlatGroundHandler
from surroundings.osm.osm_water_handler import OSMRiversPolygonsHandler
from surroundings.swisstopo import (
    SwissTopoBuildingSurroundingHandler,
    SwisstopoElevationHandler,
    SwissTopoExtraLakesSurroundingHandler,
    SwissTopoForestSurroundingHandler,
    SwissTopoGroundSurroundingHandler,
    SwissTopoLakeSurroundingHandler,
    SwissTopoMountainSurroundingHandler,
    SwissTopoParksSurroundingHandler,
    SwissTopoRailroadSurroundingHandler,
    SwissTopoRiverSurroundingHandler,
    SwissTopoStreetSurroundingHandler,
    SwissTopoTreeSurroundingHandler,
)
from surroundings.triangle_remover import TriangleRemover
from surroundings.utils import SurrTrianglesType


class ManualSurroundingsHandler:
    @classmethod
    def _apply_exclusion_polygon(
        cls, site_id: int, region: REGION, triangles: Iterator[SurrTrianglesType]
    ) -> Iterator[SurrTrianglesType]:
        if exclusion_footprint := ManualExclusionSurroundingHandler(
            site_id=site_id, region=region
        ).get_footprint():
            yield from TriangleRemover.exclude_2d_intersections(
                footprint=exclusion_footprint,
                triangles=triangles,
            )
        else:
            yield from triangles

    @classmethod
    def _generate_manual_surroundings(
        cls,
        site_id: int,
        region: REGION,
        layout_footprint: Polygon | MultiPolygon,
        elevation_handler: BaseElevationHandler,
    ) -> Iterator[SurrTrianglesType]:
        triangles = ManualBuildingSurroundingHandler(
            site_id=site_id,
            region=region,
            elevation_handler=elevation_handler,
        ).get_triangles()
        yield from TriangleRemover.exclude_2d_intersections(
            footprint=layout_footprint,
            triangles=triangles,
        )

    @classmethod
    def apply_manual_adjustments(
        cls,
        site_id: int,
        region: REGION,
        triangles: Iterator[SurrTrianglesType],
        elevation_handler: BaseElevationHandler,
        building_footprints: list[Polygon | MultiPolygon],
    ) -> Iterator[SurrTrianglesType]:
        yield from cls._apply_exclusion_polygon(
            site_id=site_id, region=region, triangles=triangles
        )
        safety_buffer = 0.1
        layout_footprint = unary_union(building_footprints).buffer(
            distance=safety_buffer,
            cap_style=CAP_STYLE.square,
            join_style=JOIN_STYLE.mitre,
        )
        yield from cls._generate_manual_surroundings(
            site_id=site_id,
            region=region,
            layout_footprint=layout_footprint,
            elevation_handler=elevation_handler,
        )


class SurroundingStorageHandler:
    DUMP_SIZE = 1000

    @staticmethod
    def load(
        filepath: Path,
    ) -> Iterator[SurrTrianglesType]:
        def read_triangles_from_csv_row(row: list[str]):
            triangles = tuple(float(i) for i in row[1:10])
            return [triangles[0:3], triangles[3:6], triangles[6:9]]

        with filepath.open(mode="r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            for row in csv_reader:
                yield SurroundingType[row[0]], read_triangles_from_csv_row(row=row)

    @classmethod
    @timer(logger=logger)
    def dump(
        cls,
        filepath: Path,
        triangles: Iterator[SurrTrianglesType],
    ):
        def flatten_triangle(
            triangle: list[tuple[float, float, float]]
        ) -> Iterator[float]:
            return (value for point in triangle for value in point)

        with filepath.open(mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=";")
            for chunk in chunker(triangles, cls.DUMP_SIZE):
                rows = (
                    (surrounding_type.name, *flatten_triangle(triangle))
                    for surrounding_type, triangle in chunk
                )
                csv_writer.writerows(rows)

    @classmethod
    def upload(cls, triangles: Iterator[SurrTrianglesType], remote_path: Path):
        """We are uploading a zip file with the content as defined in the remote path (.zip), which includes a
        unique name as uuid4 to be able to later extract the file content without local collisions
        """
        with NamedTemporaryFile() as f:
            csv_file_path = Path(f.name)
            cls.dump(
                filepath=csv_file_path,
                triangles=triangles,
            )
            compressed_file = Path(f.name).with_suffix(".zip")
            with ZipFile(
                file=compressed_file.as_posix(),
                mode="w",
                compression=ZIP_DEFLATED,
                compresslevel=9,
            ) as myzip:
                myzip.write(
                    csv_file_path.as_posix(),
                    arcname=f"{uuid4().hex}.csv",
                )

            GCloudStorageHandler().upload_file_to_bucket(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                destination_folder=GOOGLE_CLOUD_VIEW_SURROUNDINGS,
                local_file_path=compressed_file,
                destination_file_name=remote_path.name,
            )

    @staticmethod
    def _download_uncompress_surroundings_to_folder(
        remote_path: Path, local_folder: Path
    ) -> Path:
        zip_file_path = local_folder.joinpath(remote_path.stem).with_suffix(".zip")
        GCloudStorageHandler().download_file(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            remote_file_path=remote_path,
            local_file_name=zip_file_path,
        )
        with ZipFile(zip_file_path) as myzip:
            surroundings_file_member = myzip.namelist()[0]
            extracted_tmp_location = Path(
                myzip.extract(
                    member=surroundings_file_member,
                    path=local_folder,
                )
            )
        return extracted_tmp_location

    @classmethod
    def read_from_cloud(cls, remote_path: Path) -> Iterator[SurrTrianglesType]:
        with TemporaryDirectory() as temp_dir:
            surr_csv_path = cls._download_uncompress_surroundings_to_folder(
                remote_path=remote_path, local_folder=Path(temp_dir)
            )

            yield from cls.load(filepath=surr_csv_path)


class SwissTopoSurroundingHandler:
    @staticmethod
    def get_building_triangles(
        location: Point,
        building_footprints: list[MultiPolygon],
        simulation_version,
        bounding_box_extension: int = None,
    ) -> Iterator[SurrTrianglesType]:
        return SwissTopoBuildingSurroundingHandler(
            location=location,
            simulation_version=simulation_version,
            bounding_box_extension=bounding_box_extension,
        ).get_triangles(building_footprints=building_footprints)

    @classmethod
    def generate_view_surroundings(
        cls,
        location: Point,
        building_footprints: list[MultiPolygon | Polygon],
        simulation_version: SIMULATION_VERSION,
        region: REGION = REGION.CH,
        site_id: Optional[int] = None,
        bounding_box_extension: int = None,
        include_mountains: bool = True,
    ) -> Iterator[SurrTrianglesType]:
        SURROUNDINGS_DIR.mkdir(parents=True, exist_ok=True)

        common_args = dict(
            location=location,
            simulation_version=simulation_version,
            bounding_box_extension=bounding_box_extension,
        )
        nearby_surrounding_triangles = chain(
            SwissTopoForestSurroundingHandler(**common_args).get_triangles(
                building_footprints=building_footprints
            ),
            SwissTopoTreeSurroundingHandler(**common_args).get_triangles(
                building_footprints=building_footprints
            ),
            cls.get_building_triangles(
                **common_args,
                building_footprints=building_footprints,
            ),
            SwissTopoParksSurroundingHandler(**common_args).get_triangles(),
            SwissTopoRailroadSurroundingHandler(**common_args).get_triangles(),
            SwissTopoRiverSurroundingHandler(**common_args).get_triangles(),
            SwissTopoStreetSurroundingHandler(**common_args).get_triangles(),
            SwissTopoLakeSurroundingHandler(**common_args).get_triangles(),
            SwissTopoExtraLakesSurroundingHandler(**common_args).get_triangles(),
        )

        if site_id:
            yield from ManualSurroundingsHandler.apply_manual_adjustments(
                site_id=site_id,
                region=region,
                building_footprints=building_footprints,
                triangles=nearby_surrounding_triangles,
                elevation_handler=SwisstopoElevationHandler(
                    location=location,
                    region=region,
                    simulation_version=simulation_version,
                ),
            )
        else:
            yield from nearby_surrounding_triangles

        yield from SwissTopoGroundSurroundingHandler(
            **common_args,
            region=region,
            building_footprints=building_footprints,
        ).get_triangles()

        if include_mountains:
            yield from SwissTopoMountainSurroundingHandler(
                location=location,
                simulation_version=simulation_version,
            ).get_triangles()


class OSMSurroundingHandler:
    @classmethod
    def generate_view_surroundings(
        cls,
        location: Point,
        building_footprints: list[MultiPolygon | Polygon],
        region: Optional[REGION] = REGION.CH,
        simulation_version: Optional[
            SIMULATION_VERSION
        ] = SIMULATION_VERSION.PH_01_2021,
        site_id: Optional[int] = None,
        bounding_box_extension: Optional[int] = None,
        include_mountains: Optional[bool] = True,
    ) -> Iterator[SurrTrianglesType]:
        SURROUNDINGS_DIR.mkdir(parents=True, exist_ok=True)

        common_args = dict(
            location=location,
            region=region,
            simulation_version=simulation_version,
            bounding_box_extension=bounding_box_extension,
        )
        elevation_handler = cls._get_elevation_handler(**common_args)
        surrounding_args = dict(
            **common_args,
            raster_grid=cls._get_raster_grid(**common_args),
            elevation_handler=elevation_handler,
        )

        yield from OSMGroundsHandler(
            **common_args,
            building_footprints=building_footprints,
        ).get_triangles()

        nearby_surrounding_triangles = chain(
            OSMStreetHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMLakesHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMRiversPolygonsHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMRiversHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMRailwayHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMParksHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMForestHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMSeaHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMBuildingsHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
            OSMTreesHandler(**surrounding_args).get_triangles(
                building_footprints=building_footprints
            ),
        )

        if site_id:
            yield from ManualSurroundingsHandler.apply_manual_adjustments(
                site_id=site_id,
                region=region,
                building_footprints=building_footprints,
                elevation_handler=elevation_handler,
                triangles=nearby_surrounding_triangles,
            )
        else:
            yield from nearby_surrounding_triangles

    @classmethod
    def _get_raster_grid(
        cls,
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        bounding_box_extension: Optional[int] = None,
    ):
        osm_ground_handler = OSMGroundsHandler(
            location=location,
            region=region,
            simulation_version=simulation_version,
            bounding_box_extension=bounding_box_extension
            or BOUNDING_BOX_EXTENSION_GROUNDS,
        )
        if not isinstance(osm_ground_handler.ground_handler, FlatGroundHandler):
            return STRtree(
                Polygon(triangle) for _, triangle in osm_ground_handler.get_triangles()
            )

    @staticmethod
    def _get_elevation_handler(
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        bounding_box_extension: Optional[int] = None,
    ):
        return get_elevation_handler(
            location=location,
            region=region,
            simulation_version=simulation_version,
            bounding_box_extension=bounding_box_extension
            or BOUNDING_BOX_EXTENSION_GROUNDS,
        )


def generate_view_surroundings(
    region: REGION,
    location: Point,
    building_footprints: list[Polygon | MultiPolygon],
    simulation_version: SIMULATION_VERSION,
    site_id: int | None = None,
    surroundings_source: SURROUNDING_SOURCES | None = None,
    sample: bool = False,
):
    from surroundings.v2.surrounding_handler import (
        OSMSlamSurroundingHandler as OSMSlamSurroundingHandlerNewSimVersion,
    )
    from surroundings.v2.surrounding_handler import (
        OSMSurroundingHandler as OSMSurroundingHandlerNewSimVersion,
    )
    from surroundings.v2.surrounding_handler import (
        SwissTopoSlamSurroundingHandler as SwissTopoSlamSurroundingHandlerNewSimVersion,
    )
    from surroundings.v2.surrounding_handler import (
        SwissTopoSurroundingHandler as SwissTopoSurroundingHandlerNewSimVersion,
    )

    if surroundings_source == SURROUNDING_SOURCES.SWISSTOPO and region != REGION.CH:
        raise AttributeError(
            f"Source {surroundings_source.value} is only supported for {REGION.CH}."
        )
    if surroundings_source in (SURROUNDING_SOURCES.SWISSTOPO, SURROUNDING_SOURCES.OSM):
        use_source = surroundings_source
    elif surroundings_source is not None:
        raise AttributeError(f"Source {surroundings_source.value} is not supported.")
    elif region == REGION.CH:
        use_source = SURROUNDING_SOURCES.SWISSTOPO
    else:
        use_source = SURROUNDING_SOURCES.OSM

    if simulation_version in (
        SIMULATION_VERSION.EXPERIMENTAL,
        SIMULATION_VERSION.PH_2022_H1,
    ):
        common_args = dict(
            region=region,
            location=location,
            building_footprints=building_footprints,
            sample=sample,
        )
        if site_id:
            handler_cls = (
                SwissTopoSlamSurroundingHandlerNewSimVersion
                if use_source == SURROUNDING_SOURCES.SWISSTOPO
                else OSMSlamSurroundingHandlerNewSimVersion
            )
            return handler_cls(
                site_id=site_id, **common_args
            ).generate_view_surroundings()

        handler_cls = (
            SwissTopoSurroundingHandlerNewSimVersion
            if use_source == SURROUNDING_SOURCES.SWISSTOPO
            else OSMSurroundingHandlerNewSimVersion
        )
        return handler_cls(**common_args).generate_view_surroundings()

    elif simulation_version == SIMULATION_VERSION.PH_01_2021:
        if use_source == SURROUNDING_SOURCES.SWISSTOPO:
            handler_cls = SwissTopoSurroundingHandler
        else:
            handler_cls = OSMSurroundingHandler

        return handler_cls.generate_view_surroundings(
            site_id=site_id,
            region=region,
            location=location,
            building_footprints=building_footprints,
            simulation_version=simulation_version,
            bounding_box_extension=(BOUNDING_BOX_EXTENSION_SAMPLE if sample else None),
            include_mountains=not sample,
        )
    raise AttributeError(
        f"Simulation version {simulation_version.value} is not supported."
    )
