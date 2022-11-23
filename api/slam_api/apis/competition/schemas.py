from marshmallow import Schema, fields, validate
from numpy import linspace

from common_utils.competition_constants import SERVICE_ROOM_TYPES, CompetitionFeatures
from common_utils.constants import CURRENCY
from slam_api.serialization import CapitalizedStr, UnionField

PercentageField = fields.Number(validate=validate.Range(0.0, 1.0))
ApartmentTypeField = fields.Number(
    validate=validate.OneOf(linspace(1, 7, num=13))
)  # from 1 to 7, step 0.5


class WeightsPutArgs(Schema):
    architecture_usage = fields.Number()
    architecture_room_programme = fields.Number()
    environmental = fields.Number()
    further_key_figures = fields.Number()


class FlatTypesDistribution(Schema):
    """
    [
        {"apartment_type": [3.5], "percentage": 0.5},
        {"apartment_type": [4.5], "percentage": 0.5},
    ]
    """

    apartment_type = fields.List(ApartmentTypeField)
    percentage = UnionField([PercentageField, fields.List(PercentageField)])


class FlatTypesAreaFulfillment(Schema):
    """
    [
        {"apartment_type": 3.5, "area": 50.0},
        {"apartment_type": 4.5, "area": 75.0},
    ]
    """

    apartment_type = ApartmentTypeField
    area = fields.Float(validate=validate.Range(min=0.0))


class BathroomFeatures(Schema):
    SHOWER = fields.Integer(validate=validate.Range(min=0))
    BATHTUB = fields.Integer(validate=validate.Range(min=0))
    SINK = fields.Integer(validate=validate.Range(min=0))
    TOILET = fields.Integer(validate=validate.Range(min=0))


class ShowersBathtubsDistribution(Schema):
    """
    [
        {"apartment_type": 3.5, "percentage": 0.5, "features": [{"SHOWER": 1, "BATHTUB": 1, "SINK": 1, "TOILET": 1}]},
        {"apartment_type": 4.5, "percentage": 0.5, "features": [{"SHOWER": 2, "BATHTUB": 1, "SINK": 1, "TOILET": 1}]},
    ]
    """

    apartment_type = ApartmentTypeField
    percentage = PercentageField
    features = fields.Nested(BathroomFeatures, many=True)


class BathroomsToiletsDistribution(Schema):
    """
    Example configuration
    [
        {"apartment_type": 3.5, "desired": ["BATHROOM"]},
        {"apartment_type": 4.5, "desired": ["BATHROOM"]},
        {"apartment_type": 5.5, "desired": ["BATHROOM", "TOILET"]},
        {"apartment_type": 6.5, "desired": ["BATHROOM", "BATHROOM"]},
    ]
    """

    apartment_type = ApartmentTypeField
    desired = fields.List(
        CapitalizedStr(
            required=True,
            validate=validate.OneOf(
                choices=tuple(room.name for room in SERVICE_ROOM_TYPES)
            ),
        )
    )


class ResidentialRatio(Schema):
    desired_ratio = fields.Float(
        validate=validate.Range(min=0, max=1.0, max_inclusive=True), required=False
    )
    acceptable_deviation = fields.Float(
        validate=validate.Range(min=0, max=1.0, max_inclusive=True),
        required=False,
        load_default=0.1,
        dump_default=0.1,
    )


class MinBathroomSizes(Schema):
    min_area = fields.Float(validate=validate.Range(min=0))
    min_big_side = fields.Float(validate=validate.Range(min=0))
    min_small_side = fields.Float(validate=validate.Range(min=0))


class MinRoomSizes(Schema):
    big_room_area = fields.Float(validate=validate.Range(min=0))
    big_room_side_big = fields.Float(validate=validate.Range(min=0))
    big_room_side_small = fields.Float(validate=validate.Range(min=0))
    small_room_area = fields.Float(validate=validate.Range(min=0))
    small_room_side_big = fields.Float(validate=validate.Range(min=0))
    small_room_side_small = fields.Float(validate=validate.Range(min=0))


class LivingDiningMinSizeDesired(Schema):
    """
    Example configuration
    [
        {"apartment_type": 3.5, "desired": 10},
        {"apartment_type": 4.5, "desired": 20},
    ]
    """

    apartment_type = ApartmentTypeField
    desired = fields.Float(validate=validate.Range(min=1.0))


class CompetitionParameters(Schema):
    flat_types_distribution = fields.Nested(FlatTypesDistribution, many=True)
    flat_types_distribution_acceptable_deviation = fields.Float(
        validate=validate.Range(min=0, max=1.0, max_inclusive=True), required=False
    )
    flat_types_area_fulfillment = fields.Nested(FlatTypesAreaFulfillment, many=True)
    showers_bathtubs_distribution = fields.Nested(
        ShowersBathtubsDistribution, many=True
    )
    bathrooms_toilets_distribution = fields.Nested(
        BathroomsToiletsDistribution, many=True
    )
    janitor_office_min_size = fields.Float(validate=validate.Range(min=0))
    janitor_storage_min_size = fields.Float(validate=validate.Range(min=0))
    bikes_and_prams_min_area = fields.Float(validate=validate.Range(min=0))
    bikes_boxes_count_min = fields.Integer(validate=validate.Range(min=0))
    min_reduit_size = fields.Float(validate=validate.Range(min=0))
    min_bathroom_sizes = fields.Nested(MinBathroomSizes)
    min_room_sizes = fields.Nested(MinRoomSizes)
    min_corridor_size = fields.Float(validate=validate.Range(min=0.1))
    commercial_use_desired = fields.Bool()
    residential_ratio = fields.Nested(ResidentialRatio)
    living_dining_desired_sizes_per_apt_type = fields.Nested(
        LivingDiningMinSizeDesired, many=True
    )
    min_outdoor_area_per_apt = fields.Float(validate=validate.Range(min=0))
    total_hnf_req = fields.Float(validate=validate.Range(min=1.0))
    dining_area_table_min_big_side = fields.Float(validate=validate.Range(min=1.0))
    dining_area_table_min_small_side = fields.Float(validate=validate.Range(min=1.0))


class CompetitorsPutArgs(Schema):
    evaluation_residential_use = fields.Bool()
    drying_room_size = fields.Bool()
    janitor_office_natural_light = fields.Bool()
    determining_whether_barrier_free_access_is_guaranteed = fields.Bool()
    determining_whether_minimum_dimension_requirements_are_met = fields.Bool()
    determining_whether_there_is_a_power_supply = fields.Bool()
    prams_bikes_close_to_entrance = fields.Bool()
    car_parking_spaces = fields.Bool()
    two_wheels_parking_spaces = fields.Bool()
    bike_parking_spaces = fields.Bool()
    second_basement_available = fields.Bool()
    kitchen_elements_requirement = PercentageField
    entrance_wardrobe_element_requirement = PercentageField
    bedroom_wardrobe_element_requirement = PercentageField
    sink_sizes_requirement = PercentageField
    basement_compartment_availability = fields.Bool()
    basement_compartment_size_requirement = fields.Bool()
    guess_room_size_requirement = fields.Bool()


class AdminCompetitionQueryArgs(Schema):
    client_id = fields.Int(required=True, allow_none=False)


class AdminCompetitionPostArgs(Schema):
    client_id = fields.Int(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    red_flags_enabled = fields.Boolean(required=True, allow_none=False)
    competitors = fields.List(fields.Int())
    currency = fields.String(
        required=True,
        allow_none=False,
        validate=validate.OneOf([ccy.name for ccy in CURRENCY]),
    )
    features_selected = fields.List(
        fields.String(
            validate=validate.OneOf([feature.name for feature in CompetitionFeatures]),
        )
    )
    prices_are_rent = fields.Boolean(required=False)
    configuration_parameters = fields.Nested(CompetitionParameters(partial=True))
