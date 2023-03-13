from typing import List, Optional

from pydantic import BaseModel
from typing_extensions import Literal

LITERAL_PROPERTY_SUBCODES = Literal[
    "apartment_normal",
    "apartment_maisonette",
    "apartment_attic",
    "apartment_penthouse",
    "apartment_terraced",
    "apartment_studio",
]

LITERAL_COUNTRIES = Literal["CH", "DE"]


class Room(BaseModel):
    connectivity_balcony_distance_max: Optional[float] = None
    connectivity_balcony_distance_mean: Optional[float] = None
    connectivity_balcony_distance_median: Optional[float] = None
    connectivity_balcony_distance_min: Optional[float] = None
    connectivity_balcony_distance_p20: Optional[float] = None
    connectivity_balcony_distance_p80: Optional[float] = None
    connectivity_balcony_distance_stddev: Optional[float] = None
    connectivity_bathroom_distance_max: Optional[float] = None
    connectivity_bathroom_distance_mean: Optional[float] = None
    connectivity_bathroom_distance_median: Optional[float] = None
    connectivity_bathroom_distance_min: Optional[float] = None
    connectivity_bathroom_distance_p20: Optional[float] = None
    connectivity_bathroom_distance_p80: Optional[float] = None
    connectivity_bathroom_distance_stddev: Optional[float] = None
    connectivity_betweenness_centrality_max: Optional[float] = None
    connectivity_betweenness_centrality_mean: Optional[float] = None
    connectivity_betweenness_centrality_median: Optional[float] = None
    connectivity_betweenness_centrality_min: Optional[float] = None
    connectivity_betweenness_centrality_p20: Optional[float] = None
    connectivity_betweenness_centrality_p80: Optional[float] = None
    connectivity_betweenness_centrality_stddev: Optional[float] = None
    connectivity_closeness_centrality_max: Optional[float] = None
    connectivity_closeness_centrality_mean: Optional[float] = None
    connectivity_closeness_centrality_median: Optional[float] = None
    connectivity_closeness_centrality_min: Optional[float] = None
    connectivity_closeness_centrality_p20: Optional[float] = None
    connectivity_closeness_centrality_p80: Optional[float] = None
    connectivity_closeness_centrality_stddev: Optional[float] = None
    connectivity_eigen_centrality_max: Optional[float] = None
    connectivity_eigen_centrality_mean: Optional[float] = None
    connectivity_eigen_centrality_median: Optional[float] = None
    connectivity_eigen_centrality_min: Optional[float] = None
    connectivity_eigen_centrality_p20: Optional[float] = None
    connectivity_eigen_centrality_p80: Optional[float] = None
    connectivity_eigen_centrality_stddev: Optional[float] = None
    connectivity_entrance_door_distance_max: Optional[float] = None
    connectivity_entrance_door_distance_mean: Optional[float] = None
    connectivity_entrance_door_distance_median: Optional[float] = None
    connectivity_entrance_door_distance_min: Optional[float] = None
    connectivity_entrance_door_distance_p20: Optional[float] = None
    connectivity_entrance_door_distance_p80: Optional[float] = None
    connectivity_entrance_door_distance_stddev: Optional[float] = None
    connectivity_kitchen_distance_max: Optional[float] = None
    connectivity_kitchen_distance_mean: Optional[float] = None
    connectivity_kitchen_distance_median: Optional[float] = None
    connectivity_kitchen_distance_min: Optional[float] = None
    connectivity_kitchen_distance_p20: Optional[float] = None
    connectivity_kitchen_distance_p80: Optional[float] = None
    connectivity_kitchen_distance_stddev: Optional[float] = None
    connectivity_living_dining_distance_max: Optional[float] = None
    connectivity_living_dining_distance_mean: Optional[float] = None
    connectivity_living_dining_distance_median: Optional[float] = None
    connectivity_living_dining_distance_min: Optional[float] = None
    connectivity_living_dining_distance_p20: Optional[float] = None
    connectivity_living_dining_distance_p80: Optional[float] = None
    connectivity_living_dining_distance_stddev: Optional[float] = None
    connectivity_loggia_distance_max: Optional[float] = None
    connectivity_loggia_distance_mean: Optional[float] = None
    connectivity_loggia_distance_median: Optional[float] = None
    connectivity_loggia_distance_min: Optional[float] = None
    connectivity_loggia_distance_p20: Optional[float] = None
    connectivity_loggia_distance_p80: Optional[float] = None
    connectivity_loggia_distance_stddev: Optional[float] = None
    connectivity_room_distance_max: Optional[float] = None
    connectivity_room_distance_mean: Optional[float] = None
    connectivity_room_distance_median: Optional[float] = None
    connectivity_room_distance_min: Optional[float] = None
    connectivity_room_distance_p20: Optional[float] = None
    connectivity_room_distance_p80: Optional[float] = None
    connectivity_room_distance_stddev: Optional[float] = None
    floor_has_elevator: bool
    floor_number: int
    layout_area: float
    layout_area_type: str
    layout_biggest_rectangle_length: float
    layout_biggest_rectangle_width: float
    layout_compactness: float
    layout_connects_to_bathroom: bool
    layout_connects_to_private_outdoor: bool
    layout_door_perimeter: float
    layout_has_bathtub: bool
    layout_has_entrance_door: bool
    layout_has_shower: bool
    layout_has_sink: bool
    layout_has_stairs: bool
    layout_has_toilet: bool
    layout_is_navigable: bool
    layout_mean_walllengths: Optional[float] = None
    layout_net_area: float
    layout_number_of_doors: Optional[int] = None
    layout_number_of_windows: Optional[int] = None
    layout_open_perimeter: Optional[float] = None
    layout_perimeter: Optional[float] = None
    layout_railing_perimeter: Optional[float] = None
    layout_room_count: Optional[float] = None
    layout_std_walllengths: Optional[float] = None
    layout_window_perimeter: Optional[float] = None
    noise_traffic_day: Optional[float] = None
    noise_traffic_night: Optional[float] = None
    noise_train_day: Optional[float] = None
    noise_train_night: Optional[float] = None
    sun_201803210800_max: Optional[float] = None
    sun_201803210800_mean: Optional[float] = None
    sun_201803210800_median: Optional[float] = None
    sun_201803210800_min: Optional[float] = None
    sun_201803210800_p20: Optional[float] = None
    sun_201803210800_p80: Optional[float] = None
    sun_201803210800_stddev: Optional[float] = None
    sun_201803211000_max: Optional[float] = None
    sun_201803211000_mean: Optional[float] = None
    sun_201803211000_median: Optional[float] = None
    sun_201803211000_min: Optional[float] = None
    sun_201803211000_p20: Optional[float] = None
    sun_201803211000_p80: Optional[float] = None
    sun_201803211000_stddev: Optional[float] = None
    sun_201803211200_max: Optional[float] = None
    sun_201803211200_mean: Optional[float] = None
    sun_201803211200_median: Optional[float] = None
    sun_201803211200_min: Optional[float] = None
    sun_201803211200_p20: Optional[float] = None
    sun_201803211200_p80: Optional[float] = None
    sun_201803211200_stddev: Optional[float] = None
    sun_201803211400_max: Optional[float] = None
    sun_201803211400_mean: Optional[float] = None
    sun_201803211400_median: Optional[float] = None
    sun_201803211400_min: Optional[float] = None
    sun_201803211400_p20: Optional[float] = None
    sun_201803211400_p80: Optional[float] = None
    sun_201803211400_stddev: Optional[float] = None
    sun_201803211600_max: Optional[float] = None
    sun_201803211600_mean: Optional[float] = None
    sun_201803211600_median: Optional[float] = None
    sun_201803211600_min: Optional[float] = None
    sun_201803211600_p20: Optional[float] = None
    sun_201803211600_p80: Optional[float] = None
    sun_201803211600_stddev: Optional[float] = None
    sun_201803211800_max: Optional[float] = None
    sun_201803211800_mean: Optional[float] = None
    sun_201803211800_median: Optional[float] = None
    sun_201803211800_min: Optional[float] = None
    sun_201803211800_p20: Optional[float] = None
    sun_201803211800_p80: Optional[float] = None
    sun_201803211800_stddev: Optional[float] = None
    sun_201806210600_max: Optional[float] = None
    sun_201806210600_mean: Optional[float] = None
    sun_201806210600_median: Optional[float] = None
    sun_201806210600_min: Optional[float] = None
    sun_201806210600_p20: Optional[float] = None
    sun_201806210600_p80: Optional[float] = None
    sun_201806210600_stddev: Optional[float] = None
    sun_201806210800_max: Optional[float] = None
    sun_201806210800_mean: Optional[float] = None
    sun_201806210800_median: Optional[float] = None
    sun_201806210800_min: Optional[float] = None
    sun_201806210800_p20: Optional[float] = None
    sun_201806210800_p80: Optional[float] = None
    sun_201806210800_stddev: Optional[float] = None
    sun_201806211000_max: Optional[float] = None
    sun_201806211000_mean: Optional[float] = None
    sun_201806211000_median: Optional[float] = None
    sun_201806211000_min: Optional[float] = None
    sun_201806211000_p20: Optional[float] = None
    sun_201806211000_p80: Optional[float] = None
    sun_201806211000_stddev: Optional[float] = None
    sun_201806211200_max: Optional[float] = None
    sun_201806211200_mean: Optional[float] = None
    sun_201806211200_median: Optional[float] = None
    sun_201806211200_min: Optional[float] = None
    sun_201806211200_p20: Optional[float] = None
    sun_201806211200_p80: Optional[float] = None
    sun_201806211200_stddev: Optional[float] = None
    sun_201806211400_max: Optional[float] = None
    sun_201806211400_mean: Optional[float] = None
    sun_201806211400_median: Optional[float] = None
    sun_201806211400_min: Optional[float] = None
    sun_201806211400_p20: Optional[float] = None
    sun_201806211400_p80: Optional[float] = None
    sun_201806211400_stddev: Optional[float] = None
    sun_201806211600_max: Optional[float] = None
    sun_201806211600_mean: Optional[float] = None
    sun_201806211600_median: Optional[float] = None
    sun_201806211600_min: Optional[float] = None
    sun_201806211600_p20: Optional[float] = None
    sun_201806211600_p80: Optional[float] = None
    sun_201806211600_stddev: Optional[float] = None
    sun_201806211800_max: Optional[float] = None
    sun_201806211800_mean: Optional[float] = None
    sun_201806211800_median: Optional[float] = None
    sun_201806211800_min: Optional[float] = None
    sun_201806211800_p20: Optional[float] = None
    sun_201806211800_p80: Optional[float] = None
    sun_201806211800_stddev: Optional[float] = None
    sun_201806212000_max: Optional[float] = None
    sun_201806212000_mean: Optional[float] = None
    sun_201806212000_median: Optional[float] = None
    sun_201806212000_min: Optional[float] = None
    sun_201806212000_p20: Optional[float] = None
    sun_201806212000_p80: Optional[float] = None
    sun_201806212000_stddev: Optional[float] = None
    sun_201812211000_max: Optional[float] = None
    sun_201812211000_mean: Optional[float] = None
    sun_201812211000_median: Optional[float] = None
    sun_201812211000_min: Optional[float] = None
    sun_201812211000_p20: Optional[float] = None
    sun_201812211000_p80: Optional[float] = None
    sun_201812211000_stddev: Optional[float] = None
    sun_201812211200_max: Optional[float] = None
    sun_201812211200_mean: Optional[float] = None
    sun_201812211200_median: Optional[float] = None
    sun_201812211200_min: Optional[float] = None
    sun_201812211200_p20: Optional[float] = None
    sun_201812211200_p80: Optional[float] = None
    sun_201812211200_stddev: Optional[float] = None
    sun_201812211400_max: Optional[float] = None
    sun_201812211400_mean: Optional[float] = None
    sun_201812211400_median: Optional[float] = None
    sun_201812211400_min: Optional[float] = None
    sun_201812211400_p20: Optional[float] = None
    sun_201812211400_p80: Optional[float] = None
    sun_201812211400_stddev: Optional[float] = None
    sun_201812211600_max: Optional[float] = None
    sun_201812211600_mean: Optional[float] = None
    sun_201812211600_median: Optional[float] = None
    sun_201812211600_min: Optional[float] = None
    sun_201812211600_p20: Optional[float] = None
    sun_201812211600_p80: Optional[float] = None
    sun_201812211600_stddev: Optional[float] = None
    view_buildings_max: Optional[float] = None
    view_buildings_mean: Optional[float] = None
    view_buildings_median: Optional[float] = None
    view_buildings_min: Optional[float] = None
    view_buildings_p20: Optional[float] = None
    view_buildings_p80: Optional[float] = None
    view_buildings_stddev: Optional[float] = None
    view_greenery_max: Optional[float] = None
    view_greenery_mean: Optional[float] = None
    view_greenery_median: Optional[float] = None
    view_greenery_min: Optional[float] = None
    view_greenery_p20: Optional[float] = None
    view_greenery_p80: Optional[float] = None
    view_greenery_stddev: Optional[float] = None
    view_ground_max: Optional[float] = None
    view_ground_mean: Optional[float] = None
    view_ground_median: Optional[float] = None
    view_ground_min: Optional[float] = None
    view_ground_p20: Optional[float] = None
    view_ground_p80: Optional[float] = None
    view_ground_stddev: Optional[float] = None
    view_highways_max: Optional[float] = None
    view_highways_mean: Optional[float] = None
    view_highways_median: Optional[float] = None
    view_highways_min: Optional[float] = None
    view_highways_p20: Optional[float] = None
    view_highways_p80: Optional[float] = None
    view_highways_stddev: Optional[float] = None
    view_isovist_max: Optional[float] = None
    view_isovist_mean: Optional[float] = None
    view_isovist_median: Optional[float] = None
    view_isovist_min: Optional[float] = None
    view_isovist_p20: Optional[float] = None
    view_isovist_p80: Optional[float] = None
    view_isovist_stddev: Optional[float] = None
    view_mountains_class_1_max: Optional[float] = None
    view_mountains_class_1_mean: Optional[float] = None
    view_mountains_class_1_median: Optional[float] = None
    view_mountains_class_1_min: Optional[float] = None
    view_mountains_class_1_p20: Optional[float] = None
    view_mountains_class_1_p80: Optional[float] = None
    view_mountains_class_1_stddev: Optional[float] = None
    view_mountains_class_2_max: Optional[float] = None
    view_mountains_class_2_mean: Optional[float] = None
    view_mountains_class_2_median: Optional[float] = None
    view_mountains_class_2_min: Optional[float] = None
    view_mountains_class_2_p20: Optional[float] = None
    view_mountains_class_2_p80: Optional[float] = None
    view_mountains_class_2_stddev: Optional[float] = None
    view_mountains_class_3_max: Optional[float] = None
    view_mountains_class_3_mean: Optional[float] = None
    view_mountains_class_3_median: Optional[float] = None
    view_mountains_class_3_min: Optional[float] = None
    view_mountains_class_3_p20: Optional[float] = None
    view_mountains_class_3_p80: Optional[float] = None
    view_mountains_class_3_stddev: Optional[float] = None
    view_mountains_class_4_max: Optional[float] = None
    view_mountains_class_4_mean: Optional[float] = None
    view_mountains_class_4_median: Optional[float] = None
    view_mountains_class_4_min: Optional[float] = None
    view_mountains_class_4_p20: Optional[float] = None
    view_mountains_class_4_p80: Optional[float] = None
    view_mountains_class_4_stddev: Optional[float] = None
    view_mountains_class_5_max: Optional[float] = None
    view_mountains_class_5_mean: Optional[float] = None
    view_mountains_class_5_median: Optional[float] = None
    view_mountains_class_5_min: Optional[float] = None
    view_mountains_class_5_p20: Optional[float] = None
    view_mountains_class_5_p80: Optional[float] = None
    view_mountains_class_5_stddev: Optional[float] = None
    view_mountains_class_6_max: Optional[float] = None
    view_mountains_class_6_mean: Optional[float] = None
    view_mountains_class_6_median: Optional[float] = None
    view_mountains_class_6_min: Optional[float] = None
    view_mountains_class_6_p20: Optional[float] = None
    view_mountains_class_6_p80: Optional[float] = None
    view_mountains_class_6_stddev: Optional[float] = None
    view_mountains_class_7_max: Optional[float] = None
    view_mountains_class_7_mean: Optional[float] = None
    view_mountains_class_7_median: Optional[float] = None
    view_mountains_class_7_min: Optional[float] = None
    view_mountains_class_7_p20: Optional[float] = None
    view_mountains_class_7_p80: Optional[float] = None
    view_mountains_class_7_stddev: Optional[float] = None
    view_pedestrians_max: Optional[float] = None
    view_pedestrians_mean: Optional[float] = None
    view_pedestrians_median: Optional[float] = None
    view_pedestrians_min: Optional[float] = None
    view_pedestrians_p20: Optional[float] = None
    view_pedestrians_p80: Optional[float] = None
    view_pedestrians_stddev: Optional[float] = None
    view_primary_streets_max: Optional[float] = None
    view_primary_streets_mean: Optional[float] = None
    view_primary_streets_median: Optional[float] = None
    view_primary_streets_min: Optional[float] = None
    view_primary_streets_p20: Optional[float] = None
    view_primary_streets_p80: Optional[float] = None
    view_primary_streets_stddev: Optional[float] = None
    view_railway_tracks_max: Optional[float] = None
    view_railway_tracks_mean: Optional[float] = None
    view_railway_tracks_median: Optional[float] = None
    view_railway_tracks_min: Optional[float] = None
    view_railway_tracks_p20: Optional[float] = None
    view_railway_tracks_p80: Optional[float] = None
    view_railway_tracks_stddev: Optional[float] = None
    view_secondary_streets_max: Optional[float] = None
    view_secondary_streets_mean: Optional[float] = None
    view_secondary_streets_median: Optional[float] = None
    view_secondary_streets_min: Optional[float] = None
    view_secondary_streets_p20: Optional[float] = None
    view_secondary_streets_p80: Optional[float] = None
    view_secondary_streets_stddev: Optional[float] = None
    view_site_max: Optional[float] = None
    view_site_mean: Optional[float] = None
    view_site_median: Optional[float] = None
    view_site_min: Optional[float] = None
    view_site_p20: Optional[float] = None
    view_site_p80: Optional[float] = None
    view_site_stddev: Optional[float] = None
    view_sky_max: Optional[float] = None
    view_sky_mean: Optional[float] = None
    view_sky_median: Optional[float] = None
    view_sky_min: Optional[float] = None
    view_sky_p20: Optional[float] = None
    view_sky_p80: Optional[float] = None
    view_sky_stddev: Optional[float] = None
    view_tertiary_streets_max: Optional[float] = None
    view_tertiary_streets_mean: Optional[float] = None
    view_tertiary_streets_median: Optional[float] = None
    view_tertiary_streets_min: Optional[float] = None
    view_tertiary_streets_p20: Optional[float] = None
    view_tertiary_streets_p80: Optional[float] = None
    view_tertiary_streets_stddev: Optional[float] = None
    view_water_max: Optional[float] = None
    view_water_mean: Optional[float] = None
    view_water_median: Optional[float] = None
    view_water_min: Optional[float] = None
    view_water_p20: Optional[float] = None
    view_water_p80: Optional[float] = None
    view_water_stddev: Optional[float] = None
    window_noise_traffic_day_max: Optional[float] = None
    window_noise_traffic_day_min: Optional[float] = None
    window_noise_traffic_night_max: Optional[float] = None
    window_noise_traffic_night_min: Optional[float] = None
    window_noise_train_day_max: Optional[float] = None
    window_noise_train_day_min: Optional[float] = None
    window_noise_train_night_max: Optional[float] = None
    window_noise_train_night_min: Optional[float] = None


class Unit(BaseModel):
    unit_id: str
    city: str
    post_code: str
    street: str
    house_number: str
    building_year: int
    country: Literal[LITERAL_COUNTRIES]
    property_subcode: Literal[LITERAL_PROPERTY_SUBCODES]
    room_simulations: List[Room]


class ValuationRequest(BaseModel):
    project_id: str
    units: List[Unit]


class ValuationResponse(BaseModel):
    unit_id: List[str]
    adjustment_factor: List[float]
    avm_valuation: List[float]
    final_valuation: List[float]
