from flask import Flask, request


def _cors(response):
    origin = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Origin"] = origin

    allowed_verbs = "GET, HEAD, POST, OPTIONS, PUT, PATCH, DELETE"
    response.headers["Access-Control-Allow-Methods"] = allowed_verbs
    response.headers["Access-Control-Allow-Credentials"] = "true"
    allowed_headers = ", ".join(("content-type", "authorization", "origin", "accept"))
    response.headers["Access-Control-Request-Headers"] = allowed_headers
    response.headers["access-control-allow-headers"] = allowed_headers

    return response


def _http_no_cache(response):
    """
    Ensure there is no HTTP caching.
    """
    if "Cache-Control" in response.headers:
        return response
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def setup_cors(application: Flask):
    application.after_request(_http_no_cache)
    application.after_request(_cors)
