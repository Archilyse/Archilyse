import mimetypes
from typing import Dict

from slam_api.apis.potential.schemas import (
    ApiUserBearerSchema,
    ApiUserLoginSchema,
    PotentialSimulationRequestSchema,
    SimulationAPISchema,
)

potential_simulation_request_args = dict(
    schema=PotentialSimulationRequestSchema,
    location="querystring",
    as_kwargs=True,
    required=True,
)

simulation_response = dict(
    schema=SimulationAPISchema,
    description="Returns the simulation results of the requested location",
    example=dict(
        sim_type="view",
        lat=47.38711,
        lon=8.575098,
        floor_number=2,
        building_footprint="POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))",
        result={
            "sky": [
                0.9864790927299936,
                1.1514270825924058,
                1.267312756760063,
                1.3233246995719554,
            ],
            "site": [
                8.933890342712402,
                8.163457870483398,
                7.828802108764648,
                7.622959136962891,
            ],
            "water": [0.0, 0.0, 0.0, 0.0],
            "ground": [
                1.7672404050827026,
                2.1588563919067383,
                2.331644296646118,
                2.427321434020996,
            ],
            "isovist": [39442.42578125, 41376.3203125, 45948.16015625, 59937.421875],
            "greenery": [
                0.5294528007507324,
                0.6280086636543274,
                0.6462430953979492,
                0.6931418180465698,
            ],
            "highways": [0, 0, 0, 0],
            "buildings": [
                0.3447660207748413,
                0.45777595043182373,
                0.48596346378326416,
                0.4928393065929413,
            ],
            "pedestrians": [
                0.004308243747800589,
                0.0066109467297792435,
                0.005935719236731529,
                0.006548753939568996,
            ],
            "railway_tracks": [0.0, 0.0, 0.0, 0.0],
            "primary_streets": [0.0, 0.0, 0.0, 0.0],
            "tertiary_streets": [
                0.000233708560699597,
                0.000233708560699597,
                0.00046917377039790154,
                0.00023546522425021976,
            ],
            "mountains_class_1": [0, 0, 0, 0],
            "mountains_class_2": [0, 0, 0, 0],
            "mountains_class_3": [0.0, 0.0, 0.0, 0.0],
            "mountains_class_4": [0.0, 0.0, 0.0, 0.0],
            "mountains_class_5": [0.0, 0.0, 0.0, 0.0],
            "mountains_class_6": [0.0, 0.0, 0.0, 0.0],
            "secondary_streets": [0, 0, 0, 0],
            "observation_points": [
                {
                    "lat": 46.004101095487925,
                    "lon": 8.959659684561096,
                    "height": 280.76486828809897,
                },
                {
                    "lat": 46.00410092107801,
                    "lon": 8.959672590605486,
                    "height": 280.76486828809897,
                },
                {
                    "lat": 46.004100746666644,
                    "lon": 8.959685496649794,
                    "height": 280.76486828809897,
                },
                {
                    "lat": 46.00410057225376,
                    "lon": 8.959698402694022,
                    "height": 280.76486828809897,
                },
            ],
        },
    ),
)


unprocessable_entity_response = dict(
    description="The requestor sent data in payload that failed the request schema validation.",
    example={
        "code": 422,
        "errors": {"password": ["Missing data for required field."]},
        "status": "Unprocessable Entity",
    },
)

wrong_credentials_response = dict(
    description="The requestor has provided wrong credentials and can't be presented with a Bearer token.",
    example=dict(msg="Wrong credentials."),
)

bearer_security_scheme: Dict = dict(security=[dict(bearer=[])])

post_auth_response = dict(
    schema=ApiUserBearerSchema,
    example=dict(
        access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODAzMTIyNTcsIm5iZiI6MTU4MDMxMjI1NywianRpIjoiM2Fi"
        "ZjQ0N2EtODIwMi00MDdiLTllMjgtNWY5YTZmZWFmZWM5IiwiZXhwIjoxNTgxNjA4MjU3LCJpZGVudGl0eSI6ImFyY2hpbHlzZ"
        "SIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.bcBALu_e2JWoqBRWx3kSZGXpRhL7E4BGbWaY8Br-Iys",
        msg="Logged in as User",
    ),
)

post_auth_request = dict(
    schema=ApiUserLoginSchema,
    required=True,
    content_type=mimetypes.types_map[".json"],
    example=dict(user="User", password="password"),
)
