from brooks.util.io import BrooksSerializable


class ParametricalGeometry(BrooksSerializable):
    __serializable_fields__ = ("label", "is_rectangular", "is_circular")

    def __init__(self, input_dict=None):
        self.label = None
        self.is_rectangular = False
        self.is_circular = False

        if input_dict is not None:
            self.from_dict(input_dict)

    def from_dict(self, input_dict):
        for key, value in input_dict.items():
            if key == "label":
                self.label = value

            elif key == "is_rectangular":
                self.is_rectangular = bool(value)

            elif key == "is_circular":
                self.is_circular = bool(value)
