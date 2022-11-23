from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LayoutFeaturesSchema:
    layout_compactness: float
    layout_is_navigable: bool
    layout_mean_walllengths: float
    layout_area: float
    layout_net_area: float
    layout_room_count: float
    layout_std_walllengths: float
    layout_area_type: str
    layout_number_of_doors: int
    layout_number_of_windows: int
    layout_has_sink: bool
    layout_has_shower: bool
    layout_has_bathtub: bool
    layout_has_stairs: bool
    layout_has_entrance_door: bool
    layout_has_toilet: bool
    layout_perimeter: float
    layout_door_perimeter: float
    layout_window_perimeter: float
    layout_open_perimeter: float
    layout_railing_perimeter: float
    layout_connects_to_bathroom: bool
    layout_connects_to_private_outdoor: bool


@dataclass
class AreaVectorStatsSchema:
    # SUN
    sun_201803210800_max: Optional[float] = field(default=None)
    sun_201803210800_mean: Optional[float] = field(default=None)
    sun_201803210800_median: Optional[float] = field(default=None)
    sun_201803210800_min: Optional[float] = field(default=None)
    sun_201803210800_p20: Optional[float] = field(default=None)
    sun_201803210800_p80: Optional[float] = field(default=None)
    sun_201803210800_stddev: Optional[float] = field(default=None)
    sun_201803211000_max: Optional[float] = field(default=None)
    sun_201803211000_mean: Optional[float] = field(default=None)
    sun_201803211000_median: Optional[float] = field(default=None)
    sun_201803211000_min: Optional[float] = field(default=None)
    sun_201803211000_p20: Optional[float] = field(default=None)
    sun_201803211000_p80: Optional[float] = field(default=None)
    sun_201803211000_stddev: Optional[float] = field(default=None)
    sun_201803211200_max: Optional[float] = field(default=None)
    sun_201803211200_mean: Optional[float] = field(default=None)
    sun_201803211200_median: Optional[float] = field(default=None)
    sun_201803211200_min: Optional[float] = field(default=None)
    sun_201803211200_p20: Optional[float] = field(default=None)
    sun_201803211200_p80: Optional[float] = field(default=None)
    sun_201803211200_stddev: Optional[float] = field(default=None)
    sun_201803211400_max: Optional[float] = field(default=None)
    sun_201803211400_mean: Optional[float] = field(default=None)
    sun_201803211400_median: Optional[float] = field(default=None)
    sun_201803211400_min: Optional[float] = field(default=None)
    sun_201803211400_p20: Optional[float] = field(default=None)
    sun_201803211400_p80: Optional[float] = field(default=None)
    sun_201803211400_stddev: Optional[float] = field(default=None)
    sun_201803211600_max: Optional[float] = field(default=None)
    sun_201803211600_mean: Optional[float] = field(default=None)
    sun_201803211600_median: Optional[float] = field(default=None)
    sun_201803211600_min: Optional[float] = field(default=None)
    sun_201803211600_p20: Optional[float] = field(default=None)
    sun_201803211600_p80: Optional[float] = field(default=None)
    sun_201803211600_stddev: Optional[float] = field(default=None)
    sun_201803211800_max: Optional[float] = field(default=None)
    sun_201803211800_mean: Optional[float] = field(default=None)
    sun_201803211800_median: Optional[float] = field(default=None)
    sun_201803211800_min: Optional[float] = field(default=None)
    sun_201803211800_p20: Optional[float] = field(default=None)
    sun_201803211800_p80: Optional[float] = field(default=None)
    sun_201803211800_stddev: Optional[float] = field(default=None)
    sun_201806210600_max: Optional[float] = field(default=None)
    sun_201806210600_mean: Optional[float] = field(default=None)
    sun_201806210600_median: Optional[float] = field(default=None)
    sun_201806210600_min: Optional[float] = field(default=None)
    sun_201806210600_p20: Optional[float] = field(default=None)
    sun_201806210600_p80: Optional[float] = field(default=None)
    sun_201806210600_stddev: Optional[float] = field(default=None)
    sun_201806210800_max: Optional[float] = field(default=None)
    sun_201806210800_mean: Optional[float] = field(default=None)
    sun_201806210800_median: Optional[float] = field(default=None)
    sun_201806210800_min: Optional[float] = field(default=None)
    sun_201806210800_p20: Optional[float] = field(default=None)
    sun_201806210800_p80: Optional[float] = field(default=None)
    sun_201806210800_stddev: Optional[float] = field(default=None)
    sun_201806211000_max: Optional[float] = field(default=None)
    sun_201806211000_mean: Optional[float] = field(default=None)
    sun_201806211000_median: Optional[float] = field(default=None)
    sun_201806211000_min: Optional[float] = field(default=None)
    sun_201806211000_p20: Optional[float] = field(default=None)
    sun_201806211000_p80: Optional[float] = field(default=None)
    sun_201806211000_stddev: Optional[float] = field(default=None)
    sun_201806211200_max: Optional[float] = field(default=None)
    sun_201806211200_mean: Optional[float] = field(default=None)
    sun_201806211200_median: Optional[float] = field(default=None)
    sun_201806211200_min: Optional[float] = field(default=None)
    sun_201806211200_p20: Optional[float] = field(default=None)
    sun_201806211200_p80: Optional[float] = field(default=None)
    sun_201806211200_stddev: Optional[float] = field(default=None)
    sun_201806211400_max: Optional[float] = field(default=None)
    sun_201806211400_mean: Optional[float] = field(default=None)
    sun_201806211400_median: Optional[float] = field(default=None)
    sun_201806211400_min: Optional[float] = field(default=None)
    sun_201806211400_p20: Optional[float] = field(default=None)
    sun_201806211400_p80: Optional[float] = field(default=None)
    sun_201806211400_stddev: Optional[float] = field(default=None)
    sun_201806211600_max: Optional[float] = field(default=None)
    sun_201806211600_mean: Optional[float] = field(default=None)
    sun_201806211600_median: Optional[float] = field(default=None)
    sun_201806211600_min: Optional[float] = field(default=None)
    sun_201806211600_p20: Optional[float] = field(default=None)
    sun_201806211600_p80: Optional[float] = field(default=None)
    sun_201806211600_stddev: Optional[float] = field(default=None)
    sun_201806211800_max: Optional[float] = field(default=None)
    sun_201806211800_mean: Optional[float] = field(default=None)
    sun_201806211800_median: Optional[float] = field(default=None)
    sun_201806211800_min: Optional[float] = field(default=None)
    sun_201806211800_p20: Optional[float] = field(default=None)
    sun_201806211800_p80: Optional[float] = field(default=None)
    sun_201806211800_stddev: Optional[float] = field(default=None)
    sun_201806212000_max: Optional[float] = field(default=None)
    sun_201806212000_mean: Optional[float] = field(default=None)
    sun_201806212000_median: Optional[float] = field(default=None)
    sun_201806212000_min: Optional[float] = field(default=None)
    sun_201806212000_p20: Optional[float] = field(default=None)
    sun_201806212000_p80: Optional[float] = field(default=None)
    sun_201806212000_stddev: Optional[float] = field(default=None)
    sun_201812211000_max: Optional[float] = field(default=None)
    sun_201812211000_mean: Optional[float] = field(default=None)
    sun_201812211000_median: Optional[float] = field(default=None)
    sun_201812211000_min: Optional[float] = field(default=None)
    sun_201812211000_p20: Optional[float] = field(default=None)
    sun_201812211000_p80: Optional[float] = field(default=None)
    sun_201812211000_stddev: Optional[float] = field(default=None)
    sun_201812211200_max: Optional[float] = field(default=None)
    sun_201812211200_mean: Optional[float] = field(default=None)
    sun_201812211200_median: Optional[float] = field(default=None)
    sun_201812211200_min: Optional[float] = field(default=None)
    sun_201812211200_p20: Optional[float] = field(default=None)
    sun_201812211200_p80: Optional[float] = field(default=None)
    sun_201812211200_stddev: Optional[float] = field(default=None)
    sun_201812211400_max: Optional[float] = field(default=None)
    sun_201812211400_mean: Optional[float] = field(default=None)
    sun_201812211400_median: Optional[float] = field(default=None)
    sun_201812211400_min: Optional[float] = field(default=None)
    sun_201812211400_p20: Optional[float] = field(default=None)
    sun_201812211400_p80: Optional[float] = field(default=None)
    sun_201812211400_stddev: Optional[float] = field(default=None)
    sun_201812211600_max: Optional[float] = field(default=None)
    sun_201812211600_mean: Optional[float] = field(default=None)
    sun_201812211600_median: Optional[float] = field(default=None)
    sun_201812211600_min: Optional[float] = field(default=None)
    sun_201812211600_p20: Optional[float] = field(default=None)
    sun_201812211600_p80: Optional[float] = field(default=None)
    sun_201812211600_stddev: Optional[float] = field(default=None)
    # VIEW
    view_buildings_max: Optional[float] = field(default=None)
    view_buildings_mean: Optional[float] = field(default=None)
    view_buildings_median: Optional[float] = field(default=None)
    view_buildings_min: Optional[float] = field(default=None)
    view_buildings_p20: Optional[float] = field(default=None)
    view_buildings_p80: Optional[float] = field(default=None)
    view_buildings_stddev: Optional[float] = field(default=None)
    view_greenery_max: Optional[float] = field(default=None)
    view_greenery_mean: Optional[float] = field(default=None)
    view_greenery_median: Optional[float] = field(default=None)
    view_greenery_min: Optional[float] = field(default=None)
    view_greenery_p20: Optional[float] = field(default=None)
    view_greenery_p80: Optional[float] = field(default=None)
    view_greenery_stddev: Optional[float] = field(default=None)
    view_ground_max: Optional[float] = field(default=None)
    view_ground_mean: Optional[float] = field(default=None)
    view_ground_median: Optional[float] = field(default=None)
    view_ground_min: Optional[float] = field(default=None)
    view_ground_p20: Optional[float] = field(default=None)
    view_ground_p80: Optional[float] = field(default=None)
    view_ground_stddev: Optional[float] = field(default=None)
    view_isovist_max: Optional[float] = field(default=None)
    view_isovist_mean: Optional[float] = field(default=None)
    view_isovist_median: Optional[float] = field(default=None)
    view_isovist_min: Optional[float] = field(default=None)
    view_isovist_p20: Optional[float] = field(default=None)
    view_isovist_p80: Optional[float] = field(default=None)
    view_isovist_stddev: Optional[float] = field(default=None)
    view_mountains_class_2_max: Optional[float] = field(default=None)
    view_mountains_class_2_mean: Optional[float] = field(default=None)
    view_mountains_class_2_median: Optional[float] = field(default=None)
    view_mountains_class_2_min: Optional[float] = field(default=None)
    view_mountains_class_2_p20: Optional[float] = field(default=None)
    view_mountains_class_2_p80: Optional[float] = field(default=None)
    view_mountains_class_2_stddev: Optional[float] = field(default=None)
    view_mountains_class_3_max: Optional[float] = field(default=None)
    view_mountains_class_3_mean: Optional[float] = field(default=None)
    view_mountains_class_3_median: Optional[float] = field(default=None)
    view_mountains_class_3_min: Optional[float] = field(default=None)
    view_mountains_class_3_p20: Optional[float] = field(default=None)
    view_mountains_class_3_p80: Optional[float] = field(default=None)
    view_mountains_class_3_stddev: Optional[float] = field(default=None)
    view_mountains_class_4_max: Optional[float] = field(default=None)
    view_mountains_class_4_mean: Optional[float] = field(default=None)
    view_mountains_class_4_median: Optional[float] = field(default=None)
    view_mountains_class_4_min: Optional[float] = field(default=None)
    view_mountains_class_4_p20: Optional[float] = field(default=None)
    view_mountains_class_4_p80: Optional[float] = field(default=None)
    view_mountains_class_4_stddev: Optional[float] = field(default=None)
    view_mountains_class_5_max: Optional[float] = field(default=None)
    view_mountains_class_5_mean: Optional[float] = field(default=None)
    view_mountains_class_5_median: Optional[float] = field(default=None)
    view_mountains_class_5_min: Optional[float] = field(default=None)
    view_mountains_class_5_p20: Optional[float] = field(default=None)
    view_mountains_class_5_p80: Optional[float] = field(default=None)
    view_mountains_class_5_stddev: Optional[float] = field(default=None)
    view_mountains_class_6_max: Optional[float] = field(default=None)
    view_mountains_class_6_mean: Optional[float] = field(default=None)
    view_mountains_class_6_median: Optional[float] = field(default=None)
    view_mountains_class_6_min: Optional[float] = field(default=None)
    view_mountains_class_6_p20: Optional[float] = field(default=None)
    view_mountains_class_6_p80: Optional[float] = field(default=None)
    view_mountains_class_6_stddev: Optional[float] = field(default=None)
    view_railway_tracks_max: Optional[float] = field(default=None)
    view_railway_tracks_mean: Optional[float] = field(default=None)
    view_railway_tracks_median: Optional[float] = field(default=None)
    view_railway_tracks_min: Optional[float] = field(default=None)
    view_railway_tracks_p20: Optional[float] = field(default=None)
    view_railway_tracks_p80: Optional[float] = field(default=None)
    view_railway_tracks_stddev: Optional[float] = field(default=None)
    view_site_max: Optional[float] = field(default=None)
    view_site_mean: Optional[float] = field(default=None)
    view_site_median: Optional[float] = field(default=None)
    view_site_min: Optional[float] = field(default=None)
    view_site_p20: Optional[float] = field(default=None)
    view_site_p80: Optional[float] = field(default=None)
    view_site_stddev: Optional[float] = field(default=None)
    view_sky_max: Optional[float] = field(default=None)
    view_sky_mean: Optional[float] = field(default=None)
    view_sky_median: Optional[float] = field(default=None)
    view_sky_min: Optional[float] = field(default=None)
    view_sky_p20: Optional[float] = field(default=None)
    view_sky_p80: Optional[float] = field(default=None)
    view_sky_stddev: Optional[float] = field(default=None)
    view_tertiary_streets_max: Optional[float] = field(default=None)
    view_tertiary_streets_mean: Optional[float] = field(default=None)
    view_tertiary_streets_median: Optional[float] = field(default=None)
    view_tertiary_streets_min: Optional[float] = field(default=None)
    view_tertiary_streets_p20: Optional[float] = field(default=None)
    view_tertiary_streets_p80: Optional[float] = field(default=None)
    view_tertiary_streets_stddev: Optional[float] = field(default=None)
    view_secondary_streets_max: Optional[float] = field(default=None)
    view_secondary_streets_mean: Optional[float] = field(default=None)
    view_secondary_streets_median: Optional[float] = field(default=None)
    view_secondary_streets_min: Optional[float] = field(default=None)
    view_secondary_streets_p20: Optional[float] = field(default=None)
    view_secondary_streets_p80: Optional[float] = field(default=None)
    view_secondary_streets_stddev: Optional[float] = field(default=None)
    view_primary_streets_max: Optional[float] = field(default=None)
    view_primary_streets_mean: Optional[float] = field(default=None)
    view_primary_streets_median: Optional[float] = field(default=None)
    view_primary_streets_min: Optional[float] = field(default=None)
    view_primary_streets_p20: Optional[float] = field(default=None)
    view_primary_streets_p80: Optional[float] = field(default=None)
    view_primary_streets_stddev: Optional[float] = field(default=None)
    view_pedestrians_max: Optional[float] = field(default=None)
    view_pedestrians_mean: Optional[float] = field(default=None)
    view_pedestrians_median: Optional[float] = field(default=None)
    view_pedestrians_min: Optional[float] = field(default=None)
    view_pedestrians_p20: Optional[float] = field(default=None)
    view_pedestrians_p80: Optional[float] = field(default=None)
    view_pedestrians_stddev: Optional[float] = field(default=None)
    view_highways_max: Optional[float] = field(default=None)
    view_highways_mean: Optional[float] = field(default=None)
    view_highways_median: Optional[float] = field(default=None)
    view_highways_min: Optional[float] = field(default=None)
    view_highways_p20: Optional[float] = field(default=None)
    view_highways_p80: Optional[float] = field(default=None)
    view_highways_stddev: Optional[float] = field(default=None)
    view_water_max: Optional[float] = field(default=None)
    view_water_mean: Optional[float] = field(default=None)
    view_water_median: Optional[float] = field(default=None)
    view_water_min: Optional[float] = field(default=None)
    view_water_p20: Optional[float] = field(default=None)
    view_water_p80: Optional[float] = field(default=None)
    view_water_stddev: Optional[float] = field(default=None)
    # NOISE
    noise_traffic_day: Optional[float] = field(default=None)
    noise_traffic_night: Optional[float] = field(default=None)
    noise_train_day: Optional[float] = field(default=None)
    noise_train_night: Optional[float] = field(default=None)
    window_noise_traffic_day_min: Optional[float] = field(default=0.0)
    window_noise_traffic_day_max: Optional[float] = field(default=0.0)
    window_noise_traffic_night_min: Optional[float] = field(default=0.0)
    window_noise_traffic_night_max: Optional[float] = field(default=0.0)
    window_noise_train_day_min: Optional[float] = field(default=0.0)
    window_noise_train_day_max: Optional[float] = field(default=0.0)
    window_noise_train_night_min: Optional[float] = field(default=0.0)
    window_noise_train_night_max: Optional[float] = field(default=0.0)
    # CONNECTIVITY
    connectivity_eigen_centrality_max: Optional[float] = field(default=None)
    connectivity_eigen_centrality_mean: Optional[float] = field(default=None)
    connectivity_eigen_centrality_median: Optional[float] = field(default=None)
    connectivity_eigen_centrality_min: Optional[float] = field(default=None)
    connectivity_eigen_centrality_p20: Optional[float] = field(default=None)
    connectivity_eigen_centrality_p80: Optional[float] = field(default=None)
    connectivity_eigen_centrality_stddev: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_max: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_mean: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_median: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_min: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_p20: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_p80: Optional[float] = field(default=None)
    connectivity_entrance_door_distance_stddev: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_max: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_mean: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_median: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_min: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_p20: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_p80: Optional[float] = field(default=None)
    connectivity_betweenness_centrality_stddev: Optional[float] = field(default=None)
    connectivity_closeness_centrality_max: Optional[float] = field(default=None)
    connectivity_closeness_centrality_mean: Optional[float] = field(default=None)
    connectivity_closeness_centrality_median: Optional[float] = field(default=None)
    connectivity_closeness_centrality_min: Optional[float] = field(default=None)
    connectivity_closeness_centrality_p20: Optional[float] = field(default=None)
    connectivity_closeness_centrality_p80: Optional[float] = field(default=None)
    connectivity_closeness_centrality_stddev: Optional[float] = field(default=None)
    connectivity_room_distance_max: Optional[float] = field(default=None)
    connectivity_room_distance_mean: Optional[float] = field(default=None)
    connectivity_room_distance_median: Optional[float] = field(default=None)
    connectivity_room_distance_min: Optional[float] = field(default=None)
    connectivity_room_distance_p20: Optional[float] = field(default=None)
    connectivity_room_distance_p80: Optional[float] = field(default=None)
    connectivity_room_distance_stddev: Optional[float] = field(default=None)
    connectivity_living_dining_distance_max: Optional[float] = field(default=None)
    connectivity_living_dining_distance_mean: Optional[float] = field(default=None)
    connectivity_living_dining_distance_median: Optional[float] = field(default=None)
    connectivity_living_dining_distance_min: Optional[float] = field(default=None)
    connectivity_living_dining_distance_p20: Optional[float] = field(default=None)
    connectivity_living_dining_distance_p80: Optional[float] = field(default=None)
    connectivity_living_dining_distance_stddev: Optional[float] = field(default=None)
    connectivity_bathroom_distance_max: Optional[float] = field(default=None)
    connectivity_bathroom_distance_mean: Optional[float] = field(default=None)
    connectivity_bathroom_distance_median: Optional[float] = field(default=None)
    connectivity_bathroom_distance_min: Optional[float] = field(default=None)
    connectivity_bathroom_distance_p20: Optional[float] = field(default=None)
    connectivity_bathroom_distance_p80: Optional[float] = field(default=None)
    connectivity_bathroom_distance_stddev: Optional[float] = field(default=None)
    connectivity_kitchen_distance_max: Optional[float] = field(default=None)
    connectivity_kitchen_distance_mean: Optional[float] = field(default=None)
    connectivity_kitchen_distance_median: Optional[float] = field(default=None)
    connectivity_kitchen_distance_min: Optional[float] = field(default=None)
    connectivity_kitchen_distance_p20: Optional[float] = field(default=None)
    connectivity_kitchen_distance_p80: Optional[float] = field(default=None)
    connectivity_kitchen_distance_stddev: Optional[float] = field(default=None)
    connectivity_balcony_distance_max: Optional[float] = field(default=None)
    connectivity_balcony_distance_mean: Optional[float] = field(default=None)
    connectivity_balcony_distance_median: Optional[float] = field(default=None)
    connectivity_balcony_distance_min: Optional[float] = field(default=None)
    connectivity_balcony_distance_p20: Optional[float] = field(default=None)
    connectivity_balcony_distance_p80: Optional[float] = field(default=None)
    connectivity_balcony_distance_stddev: Optional[float] = field(default=None)
    connectivity_loggia_distance_max: Optional[float] = field(default=None)
    connectivity_loggia_distance_mean: Optional[float] = field(default=None)
    connectivity_loggia_distance_median: Optional[float] = field(default=None)
    connectivity_loggia_distance_min: Optional[float] = field(default=None)
    connectivity_loggia_distance_p20: Optional[float] = field(default=None)
    connectivity_loggia_distance_p80: Optional[float] = field(default=None)
    connectivity_loggia_distance_stddev: Optional[float] = field(default=None)


@dataclass
class BiggestRectangleSchema:
    layout_biggest_rectangle_length: Optional[float] = field(default=None)
    layout_biggest_rectangle_width: Optional[float] = field(default=None)


@dataclass
class FloorFeaturesSchema:
    floor_number: int
    floor_has_elevator: bool


@dataclass
class ApartmentId:
    apartment_id: str


@dataclass
class AreaVectorSchema(
    BiggestRectangleSchema,
    AreaVectorStatsSchema,
    FloorFeaturesSchema,
    LayoutFeaturesSchema,
    ApartmentId,
):
    pass


@dataclass
class AreaDBIdentifierSchema:
    site_id: int
    building_id: int
    floor_id: int
    unit_id: int
    area_id: int


@dataclass
class NeufertAreaVectorSchema(AreaVectorSchema, AreaDBIdentifierSchema):
    pass


@dataclass
class NeufertGeometryVectorSchema(AreaDBIdentifierSchema, ApartmentId):
    entity_type: str
    entity_subtype: str
    geometry: str
