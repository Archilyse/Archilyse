class IfcValidationException(Exception):
    pass


class IfcMapperException(Exception):
    pass


class IfcReaderException(Exception):
    pass


class IfcGeometryException(Exception):
    pass


class IfcUncoveredGeometricalRepresentation(IfcMapperException):
    """
    Exception if the ifcopenshell wrapper can not extract the geometry
    """

    pass


class IfcGeoreferencingException(Exception):
    pass
