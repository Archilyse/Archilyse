def test_access_control_applied_to_all_endpoints():
    from slam_api.apis.constants import (
        area_filters,
        constants_app,
        get_classification_scheme,
        get_classification_schemes,
    )
    from slam_api.app import app, flask_api_check, flask_api_ping

    ignore_endpoints = {
        "static",
        "api-docs.openapi_json",
        "api-docs.openapi_swagger_ui",
        "Auth.Login",
        "user.UserChangePassword",
        "user.UserForgottenPassword",
        flask_api_check.__name__,
        flask_api_ping.__name__,
        f"{constants_app.name}.{get_classification_schemes.__name__}",
        f"{constants_app.name}.{get_classification_scheme.__name__}",
        f"{constants_app.name}.{area_filters.__name__}",
    }
    ignore_endpoints.update({f"no_api_{endpoint}" for endpoint in ignore_endpoints})
    for view_name, view_function in app.view_functions.items():
        if view_name in ignore_endpoints:
            continue

        if hasattr(view_function, "view_class"):
            # If method view
            for method in view_function.view_class.methods:
                method_function = getattr(view_function.view_class, method.lower())
                assert hasattr(method_function, "__access_control__"), view_name
        else:
            assert hasattr(view_function, "__access_control__"), view_name
