from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import pkg_resources
from cycler import cycler


class ApartmentChartCategory(Enum):
    VIEW = "View"
    SUN = "Daylight"
    CENTRALITY = "Accessibility"
    PRIVACY = "Privacy"
    NOISE = "Noise"
    ROOM_LAYOUT = "Layout"
    ALL = "All"


class ApartmentChartDimension(Enum):
    VIEW_BUILDINGS = "Buildings"
    VIEW_GREENERY = "Greenery"
    VIEW_GROUND = "Ground"
    VIEW_ISOVIST = "Isovist"
    VIEW_MOUNTAINS_CLASS_2 = "Mountains >3500m"
    VIEW_MOUNTAINS_CLASS_3 = "Mountains >2500m"
    VIEW_MOUNTAINS_CLASS_4 = "Mountains >1500n"
    VIEW_MOUNTAINS_CLASS_5 = "Mountains >1000m"
    VIEW_MOUNTAINS_CLASS_6 = "Mountains >300m"
    VIEW_RAILWAY_TRACKS = "Railway Tracks"
    VIEW_SKY = "Sky"
    VIEW_TERTIARY_STREETS = "Tertiary Streets"
    VIEW_SECONDARY_STREETS = "Secondary Streets"
    VIEW_PRIMARY_STREETS = "Primary Streets"
    VIEW_PEDESTRIANS = "Pedestrians"
    VIEW_HIGHWAYS = "Highways"
    VIEW_WATER = "Water"

    SUN_201806210600 = "Daylight Summer Morning"
    SUN_201806211200 = "Daylight Summer Noon"
    SUN_201806211800 = "Daylight Summer Evening"
    SUN_201803210800 = "Daylight Equinox Morning"
    SUN_201803211200 = "Daylight Equinox Noon"
    SUN_201803211800 = "Daylight Equinox Evening"
    SUN_201812211000 = "Daylight Winter Morning"
    SUN_201812211200 = "Daylight Winter Noon"
    SUN_201812211600 = "Daylight Winter Evening"

    CONNECTIVITY_EIGEN_CENTRALITY = "Closeness Subcentre"
    CONNECTIVITY_CLOSENESS_CENTRALITY = "Closeness Centre"
    CONNECTIVITY_BETWEENNESS_CENTRALITY = "High Footfall"
    CONNECTIVITY_SECLUSION_CENTRALITY = "Seclusion"

    CONNECTIVITY_ENTRANCE_DOOR_DISTANCE = "Entrance Door Distance"
    CONNECTIVITY_ROOM_DISTANCE = "Room Distance"
    CONNECTIVITY_LIVING_DINING_DISTANCE = "Living Dining Distance"
    CONNECTIVITY_BATHROOM_DISTANCE = "Bathroom Distance"
    CONNECTIVITY_KITCHEN_DISTANCE = "Kitchen Distance"
    CONNECTIVITY_BALCONY_DISTANCE = "Balcony Distance"
    CONNECTIVITY_LOGGIA_DISTANCE = "Loggia Distance"

    WINDOW_NOISE_TRAFFIC_DAY = "Noise Traffic Day"
    WINDOW_NOISE_TRAFFIC_NIGHT = "Noise Traffic Night"
    WINDOW_NOISE_TRAIN_DAY = "Noise Train Day"
    WINDOW_NOISE_TRAIN_NIGHT = "Noise Train Night"

    ROOM_LAYOUT_WINDOW_PERIMETER = "Window Surface"
    ROOM_LAYOUT_AREA_SHARE = "Apartment Area Share"
    ROOM_LAYOUT_AREA = "Area"
    ROOM_LAYOUT_COMPACTNESS = "Compactness"
    ROOM_LAYOUT_BIGGEST_RECTANGLE = "Largest Rectangle"
    ROOM_LAYOUT_MINIMUM_ROOM_WIDTH = "Min Room Width"
    ROOM_LAYOUT_AVERAGE_WALL_WIDTH = "Average Wall Width"
    ROOM_LAYOUT_PRIVACY = "Privacy"
    ROOM_LAYOUT_HEAT_RISK = "Heat Risk"
    ROOM_LAYOUT_FUNCTIONAL_ACCESSIBILITY = "Functional Accessibility"


DIMENSION_TO_VECTOR_COLUMN = {
    ApartmentChartDimension.VIEW_BUILDINGS: "view_buildings_p80",
    ApartmentChartDimension.VIEW_GREENERY: "view_greenery_p80",
    ApartmentChartDimension.VIEW_GROUND: "view_ground_p80",
    ApartmentChartDimension.VIEW_ISOVIST: "view_isovist_p80",
    ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_2: "view_mountains_class_2_p80",
    ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_3: "view_mountains_class_3_p80",
    ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_4: "view_mountains_class_4_p80",
    ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_5: "view_mountains_class_5_p80",
    ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_6: "view_mountains_class_6_p80",
    ApartmentChartDimension.VIEW_RAILWAY_TRACKS: "view_railway_tracks_p80",
    ApartmentChartDimension.VIEW_SKY: "view_sky_p80",
    ApartmentChartDimension.VIEW_TERTIARY_STREETS: "view_tertiary_streets_p80",
    ApartmentChartDimension.VIEW_SECONDARY_STREETS: "view_secondary_streets_p80",
    ApartmentChartDimension.VIEW_PRIMARY_STREETS: "view_primary_streets_p80",
    ApartmentChartDimension.VIEW_PEDESTRIANS: "view_pedestrians_p80",
    ApartmentChartDimension.VIEW_HIGHWAYS: "view_highways_p80",
    ApartmentChartDimension.VIEW_WATER: "view_water_p80",
    ApartmentChartDimension.SUN_201806210600: "sun_201806210600_p80",
    ApartmentChartDimension.SUN_201806211200: "sun_201806211200_p80",
    ApartmentChartDimension.SUN_201806211800: "sun_201806211800_p80",
    ApartmentChartDimension.SUN_201803210800: "sun_201803210800_p80",
    ApartmentChartDimension.SUN_201803211200: "sun_201803211200_p80",
    ApartmentChartDimension.SUN_201803211800: "sun_201803211800_p80",
    ApartmentChartDimension.SUN_201812211000: "sun_201812211000_p80",
    ApartmentChartDimension.SUN_201812211200: "sun_201812211200_p80",
    ApartmentChartDimension.SUN_201812211600: "sun_201812211600_p80",
    ApartmentChartDimension.CONNECTIVITY_EIGEN_CENTRALITY: "connectivity_eigen_centrality_p80",
    ApartmentChartDimension.CONNECTIVITY_CLOSENESS_CENTRALITY: "connectivity_closeness_centrality_p80",
    ApartmentChartDimension.CONNECTIVITY_BETWEENNESS_CENTRALITY: "connectivity_betweenness_centrality_p80",
    ApartmentChartDimension.CONNECTIVITY_ENTRANCE_DOOR_DISTANCE: "connectivity_entrance_door_distance_p80",
    ApartmentChartDimension.CONNECTIVITY_ROOM_DISTANCE: "connectivity_room_distance_p80",
    ApartmentChartDimension.CONNECTIVITY_LIVING_DINING_DISTANCE: "connectivity_living_dining_distance_p80",
    ApartmentChartDimension.CONNECTIVITY_BATHROOM_DISTANCE: "connectivity_bathroom_distance_p80",
    ApartmentChartDimension.CONNECTIVITY_KITCHEN_DISTANCE: "connectivity_kitchen_distance_p80",
    ApartmentChartDimension.CONNECTIVITY_BALCONY_DISTANCE: "connectivity_balcony_distance_p80",
    ApartmentChartDimension.CONNECTIVITY_LOGGIA_DISTANCE: "connectivity_loggia_distance_p80",
    ApartmentChartDimension.WINDOW_NOISE_TRAFFIC_DAY: "window_noise_traffic_day_max",
    ApartmentChartDimension.WINDOW_NOISE_TRAFFIC_NIGHT: "window_noise_traffic_night_max",
    ApartmentChartDimension.WINDOW_NOISE_TRAIN_DAY: "window_noise_train_day_max",
    ApartmentChartDimension.WINDOW_NOISE_TRAIN_NIGHT: "window_noise_train_night_max",
    ApartmentChartDimension.ROOM_LAYOUT_WINDOW_PERIMETER: "layout_window_perimeter",
    ApartmentChartDimension.ROOM_LAYOUT_AREA: "layout_area",
    ApartmentChartDimension.ROOM_LAYOUT_BIGGEST_RECTANGLE: "room_aggregate_largest_rectangle_area",
    ApartmentChartDimension.ROOM_LAYOUT_AREA_SHARE: "room_aggregate_area_share",
    ApartmentChartDimension.ROOM_LAYOUT_COMPACTNESS: "layout_compactness",
    ApartmentChartDimension.ROOM_LAYOUT_MINIMUM_ROOM_WIDTH: "layout_biggest_rectangle_width",
    ApartmentChartDimension.ROOM_LAYOUT_AVERAGE_WALL_WIDTH: "layout_mean_walllengths",
    ApartmentChartDimension.ROOM_LAYOUT_PRIVACY: "room_aggregate_privacy",
    ApartmentChartDimension.ROOM_LAYOUT_HEAT_RISK: "room_aggregate_heat_risk",
    ApartmentChartDimension.CONNECTIVITY_SECLUSION_CENTRALITY: "room_aggregate_seclusion",
    ApartmentChartDimension.ROOM_LAYOUT_FUNCTIONAL_ACCESSIBILITY: "room_aggregate_functional_accessibility",
}


class SimulationCategoryConfiguration:
    _category: ApartmentChartCategory
    _dimensions: List[ApartmentChartDimension]
    _dimension_desirabilities: Dict[ApartmentChartDimension, float]
    _dimension_weights: Optional[Dict[ApartmentChartDimension, float]] = None

    @property
    def category_name(self):
        return self._category.value

    @property
    def columns(self) -> List[str]:
        return [DIMENSION_TO_VECTOR_COLUMN[dimension] for dimension in self._dimensions]

    @property
    def column_names(self) -> Dict[str, str]:
        return {
            DIMENSION_TO_VECTOR_COLUMN[
                dimension
            ]: f'{"Low " if self._dimension_desirabilities[dimension] < 0 else ""}'
            + dimension.value.replace(" ", "\n")
            for dimension in self._dimensions
        }

    @property
    def column_desirabilities(self) -> Dict[str, float]:
        """desirability on a range from -1 (undesirable) to +1 (desirable)"""
        return {
            DIMENSION_TO_VECTOR_COLUMN[dimension]: weight
            for dimension, weight in self._dimension_desirabilities.items()
        }

    @property
    def column_weights(self) -> Dict[str, float]:
        """weight on a range from 0 (ignore) to 1 (full weight), needs
        to be a probability distribution (i.e. sum has to be 1).

        If _dimension_weights is not set, returns uniform weights.
        """
        if self._dimension_weights is None:
            return {
                DIMENSION_TO_VECTOR_COLUMN[dimension]: 1
                / len(self._dimension_desirabilities)
                for dimension, _ in self._dimension_desirabilities.items()
            }

        return {
            DIMENSION_TO_VECTOR_COLUMN[dimension]: weight
            for dimension, weight in self._dimension_weights.items()
        }


class ViewSimulationCategoryConfiguration(SimulationCategoryConfiguration):
    _category = ApartmentChartCategory.VIEW
    _dimensions = [
        ApartmentChartDimension.VIEW_BUILDINGS,
        ApartmentChartDimension.VIEW_GREENERY,
        ApartmentChartDimension.VIEW_GROUND,
        ApartmentChartDimension.VIEW_ISOVIST,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_2,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_3,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_4,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_5,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_6,
        ApartmentChartDimension.VIEW_RAILWAY_TRACKS,
        ApartmentChartDimension.VIEW_SKY,
        ApartmentChartDimension.VIEW_TERTIARY_STREETS,
        ApartmentChartDimension.VIEW_SECONDARY_STREETS,
        ApartmentChartDimension.VIEW_PRIMARY_STREETS,
        ApartmentChartDimension.VIEW_PEDESTRIANS,
        ApartmentChartDimension.VIEW_HIGHWAYS,
        ApartmentChartDimension.VIEW_WATER,
    ]
    _dimension_desirabilities = {
        ApartmentChartDimension.VIEW_BUILDINGS: -1.0,
        ApartmentChartDimension.VIEW_GREENERY: 1.0,
        ApartmentChartDimension.VIEW_GROUND: 1.0,
        ApartmentChartDimension.VIEW_ISOVIST: 1.0,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_2: 1.0,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_3: 1.0,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_4: 1.0,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_5: 1.0,
        ApartmentChartDimension.VIEW_MOUNTAINS_CLASS_6: 1.0,
        ApartmentChartDimension.VIEW_RAILWAY_TRACKS: -1.0,
        ApartmentChartDimension.VIEW_SKY: 1.0,
        ApartmentChartDimension.VIEW_TERTIARY_STREETS: -1.0,
        ApartmentChartDimension.VIEW_SECONDARY_STREETS: -1.0,
        ApartmentChartDimension.VIEW_PRIMARY_STREETS: -1.0,
        ApartmentChartDimension.VIEW_PEDESTRIANS: 1.0,
        ApartmentChartDimension.VIEW_HIGHWAYS: -1.0,
        ApartmentChartDimension.VIEW_WATER: 1.0,
    }


class SunSimulationCategoryConfiguration(SimulationCategoryConfiguration):
    _category = ApartmentChartCategory.SUN
    _dimensions = [
        ApartmentChartDimension.SUN_201806210600,
        ApartmentChartDimension.SUN_201806211200,
        ApartmentChartDimension.SUN_201806211800,
        ApartmentChartDimension.SUN_201803211800,
        ApartmentChartDimension.SUN_201803211200,
        ApartmentChartDimension.SUN_201812211000,
        ApartmentChartDimension.SUN_201812211200,
        ApartmentChartDimension.SUN_201812211600,
    ]
    _dimension_desirabilities = {
        ApartmentChartDimension.SUN_201806210600: 1.0,
        ApartmentChartDimension.SUN_201806211200: -1.0,
        ApartmentChartDimension.SUN_201806211800: 1.0,
        ApartmentChartDimension.SUN_201803211800: 1.0,
        ApartmentChartDimension.SUN_201803211200: 1.0,
        ApartmentChartDimension.SUN_201812211000: 1.0,
        ApartmentChartDimension.SUN_201812211200: 1.0,
        ApartmentChartDimension.SUN_201812211600: 1.0,
    }


class NoiseSimulationCategoryConfiguration(SimulationCategoryConfiguration):
    _category = ApartmentChartCategory.NOISE
    _dimensions = [
        ApartmentChartDimension.WINDOW_NOISE_TRAFFIC_DAY,
        ApartmentChartDimension.WINDOW_NOISE_TRAFFIC_NIGHT,
        ApartmentChartDimension.WINDOW_NOISE_TRAIN_DAY,
        ApartmentChartDimension.WINDOW_NOISE_TRAIN_NIGHT,
    ]
    _dimension_desirabilities = {
        ApartmentChartDimension.WINDOW_NOISE_TRAFFIC_DAY: -1.0,
        ApartmentChartDimension.WINDOW_NOISE_TRAFFIC_NIGHT: -1.0,
        ApartmentChartDimension.WINDOW_NOISE_TRAIN_DAY: -1.0,
        ApartmentChartDimension.WINDOW_NOISE_TRAIN_NIGHT: -1.0,
    }


class CentralitySimulationCategoryConfiguration(SimulationCategoryConfiguration):
    _category = ApartmentChartCategory.CENTRALITY
    _dimensions = [
        ApartmentChartDimension.CONNECTIVITY_EIGEN_CENTRALITY,
        ApartmentChartDimension.CONNECTIVITY_BETWEENNESS_CENTRALITY,
        ApartmentChartDimension.CONNECTIVITY_CLOSENESS_CENTRALITY,
        ApartmentChartDimension.CONNECTIVITY_SECLUSION_CENTRALITY,
    ]
    _dimension_desirabilities = {
        ApartmentChartDimension.CONNECTIVITY_EIGEN_CENTRALITY: 1.0,
        ApartmentChartDimension.CONNECTIVITY_BETWEENNESS_CENTRALITY: 1.0,
        ApartmentChartDimension.CONNECTIVITY_CLOSENESS_CENTRALITY: 1.0,
        ApartmentChartDimension.CONNECTIVITY_SECLUSION_CENTRALITY: 1.0,
    }


class RoomLayoutSimulationCategoryConfiguration(SimulationCategoryConfiguration):
    _category = ApartmentChartCategory.ROOM_LAYOUT
    _dimensions = [
        ApartmentChartDimension.ROOM_LAYOUT_WINDOW_PERIMETER,
        ApartmentChartDimension.ROOM_LAYOUT_AREA,
        ApartmentChartDimension.ROOM_LAYOUT_BIGGEST_RECTANGLE,
        ApartmentChartDimension.ROOM_LAYOUT_AREA_SHARE,
        ApartmentChartDimension.ROOM_LAYOUT_COMPACTNESS,
        ApartmentChartDimension.ROOM_LAYOUT_MINIMUM_ROOM_WIDTH,
        ApartmentChartDimension.ROOM_LAYOUT_AVERAGE_WALL_WIDTH,
        # ApartmentChartDimension.ROOM_LAYOUT_PRIVACY,
        ApartmentChartDimension.ROOM_LAYOUT_HEAT_RISK,
        ApartmentChartDimension.ROOM_LAYOUT_FUNCTIONAL_ACCESSIBILITY,
    ]
    _dimension_desirabilities = {
        ApartmentChartDimension.ROOM_LAYOUT_WINDOW_PERIMETER: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_AREA: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_BIGGEST_RECTANGLE: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_AREA_SHARE: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_COMPACTNESS: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_MINIMUM_ROOM_WIDTH: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_AVERAGE_WALL_WIDTH: 1.0,
        # ApartmentChartDimension.ROOM_LAYOUT_PRIVACY: 1.0,
        ApartmentChartDimension.ROOM_LAYOUT_HEAT_RISK: -1.0,
        ApartmentChartDimension.ROOM_LAYOUT_FUNCTIONAL_ACCESSIBILITY: 1.0,
    }


class AllDimensionsSimulationCategoryConfiguration(SimulationCategoryConfiguration):
    _category = ApartmentChartCategory.ALL

    _CONFIGURATIONS = [
        ViewSimulationCategoryConfiguration,
        SunSimulationCategoryConfiguration,
        NoiseSimulationCategoryConfiguration,
        CentralitySimulationCategoryConfiguration,
        RoomLayoutSimulationCategoryConfiguration,
    ]

    @property
    def columns(self) -> List[str]:
        columns = []
        for configuration in self._CONFIGURATIONS:
            columns.extend(configuration().columns)
        return columns

    @property
    def column_names(self) -> Dict[str, str]:
        column_names = {}
        for configuration in self._CONFIGURATIONS:
            column_names.update(configuration().column_names)
        return column_names

    @property
    def column_desirabilities(self):
        desirabilities = {}
        for configuration in self._CONFIGURATIONS:
            desirabilities.update(configuration().column_desirabilities)
        return desirabilities

    @property
    def column_weights(self):
        """Each configuration is weighted equally, i.e. if
        one sub configuration has 5 dimensions and anotehr 10 dimensions
        then the dimensions of the former one count twice as much as the
        latter ones. This makes view count the same as nosie etc.
        """
        weights = {}
        for configuration in self._CONFIGURATIONS:
            configuration_weights = configuration().column_weights
            weights.update(
                {
                    column: weight / len(self._CONFIGURATIONS)
                    for column, weight in configuration_weights.items()
                }
            )
        return weights


class ChartType(Enum):
    UNIT_ROOM_SUMMARY = "unit_room_summary"
    UNIT_SUMMARY = "unit_summary"
    BUILDING_SUMMARY = "building_summary"


CHART_STYLE = {
    "lines.linewidth": 2,
    "lines.color": "#666666",
    "lines.markersize": 16,
    "lines.markerfacecolor": "#ffffff",
    "lines.markeredgewidth": 5,
    "lines.markeredgecolor": "#666666",
    "patch.facecolor": "#ffffff",
    "patch.edgecolor": "#666666",
    "patch.linewidth": 2,
    "font.size": 20,
    "font.family": "sans-serif",
    "font.sans-serif": "Barlow, DejaVu Sans, Bitstream Vera Sans, Computer Modern Sans Serif, Lucida Grande, Verdana, Geneva, Lucid, Arial, Helvetica, Avant Garde, sans-serif",
    "text.color": "#434343",
    "axes.edgecolor": "#666666",
    "xtick.major.size": 10,
    "xtick.labelcolor": "#434343",
    "xtick.major.pad": 1,
    "ytick.labelcolor": "#434343",
    "ytick.labelright": True,
    "ytick.labelleft": False,
    "ytick.major.pad": 24,
    "axes.prop_cycle": cycler("color", ["#666666"]),
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.facecolor": "none",
    "grid.color": "#ececec",
    "figure.figsize": (22, 39.1),
    "figure.dpi": 72,
    "figure.facecolor": "#ffffff",
    "figure.edgecolor": "#666666",
    "figure.frameon": False,
    "axes.titlesize": "xx-large",
}

FONT_DIR = Path(pkg_resources.resource_filename("handlers", "charts/fonts/"))
APARTMENT_CLUSTER_COLUMN = "apartment_aggregate_cluster"
AREA_TYPE_COLUMN = "layout_area_type"
CLUSTER_COLUMNS = [APARTMENT_CLUSTER_COLUMN, AREA_TYPE_COLUMN]
