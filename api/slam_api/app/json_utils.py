from enum import Enum

from flask.json import JSONEncoder


class SlamJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder to deal with none serializable data types.
    """

    def default(self, obj):
        try:
            if isinstance(obj, Enum):
                return obj.name

            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)

        return JSONEncoder.default(self, obj)
