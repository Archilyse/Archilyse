import copy
from http import HTTPStatus

from deepdiff import DeepDiff

from handlers.db import AreaDBHandler
from slam_api.apis.features import FeaturesView, features_app
from tests.flask_utils import get_address_for


def test_api_get_basic_features(mocker, client, site, plan, make_classified_plans):
    make_classified_plans(plan, annotations_plan_id=863)
    areas = AreaDBHandler.find(plan_id=plan["id"])

    area_find_spy = mocker.spy(AreaDBHandler, "find")
    deepcopy_spy = mocker.spy(copy, "deepcopy")

    url = get_address_for(
        blueprint=features_app,
        use_external_address=False,
        view_function=FeaturesView,
        site_id=site["id"],
        plan_id=plan["id"],
    )
    response = client.post(url, json={"areas_ids": [[a["id"] for a in areas]]})
    assert area_find_spy.call_count == 1
    # marshmallow seem to be making calls to deepcopy when the API has arguments defined, as many as types defined?
    assert deepcopy_spy.call_count == 4
    assert response.status_code == HTTPStatus.OK, response.json
    assert not DeepDiff(
        {
            "area-sia416-ANF": 4.643966788599463,
            "area-sia416-FF": 1.060709237028075,
            "area-sia416-HNF": 242.93489330923674,
            "area-sia416-NNF": 2.433488095155847,
            "area-sia416-VF": 0.0,
            "net-area": 245.36838140439258,
            "net-area-no-corridors": 200.09070479921823,
            "net-area-no-corridors-reduced-loggias": 200.09070479921823,
            "net-area-reduced-loggias": 243.54318140439256,
            "number-of-rooms": 7.0,
        },
        response.json[0],
        significant_digits=3,
    )
