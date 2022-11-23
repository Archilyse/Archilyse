from flask import Flask


class reFlask(Flask):
    def __call__(self, environ, start_response):
        """HACK: Overriding flask uswsgi call to default REQUEST_METHOD to get to avoid:
        https://archilyse.atlassian.net/browse/TECH-1443
        """
        environ["REQUEST_METHOD"] = environ.get("REQUEST_METHOD", "GET")
        return super().__call__(environ, start_response)
