import ifcopenshell


class IfcBaseType(ifcopenshell.entity_instance):
    pass


class IfcRoot(IfcBaseType):
    pass


class IfcObject(IfcRoot):
    pass


class IfcRelationship(IfcRoot):
    pass


class IfcProduct(IfcObject):
    pass


class IfcElement(IfcProduct):
    pass


class IfcSpatialElement(IfcProduct):
    pass


# Building Elements


class IfcBuildingElement(IfcElement):
    pass


class IfcWallStandardCase(IfcBuildingElement):
    pass


class IfcRailing(IfcBuildingElement):
    pass


class IfcColumn(IfcBuildingElement):
    pass


class IfcSlabStandardCase(IfcBuildingElement):
    pass


class IfcStair(IfcBuildingElement):
    pass


class IfcWindow(IfcBuildingElement):
    pass


class IfcDoor(IfcBuildingElement):
    pass


# Furniture


class IfcSanitaryTerminal(IfcElement):
    pass


class IfcFurniture(IfcElement):
    pass


# Openings


class IfcOpeningElement(IfcElement):
    pass


class IfcRelVoidsElement(IfcRelationship):
    pass


class IfcRelFillsElement(IfcRelationship):
    pass


# Spatial Structure


class IfcSpatialStructureElement(IfcElement):
    pass


class IfcSite(IfcSpatialStructureElement):
    pass


class IfcBuilding(IfcSpatialStructureElement):
    pass


class IfcBuildingStorey(IfcSpatialStructureElement):
    pass


class IfcSpace(IfcSpatialStructureElement):
    pass


class IfcSpatialZone(IfcSpatialStructureElement):
    pass


class IfcRelContainedInSpatialStructure(IfcRelationship):
    pass


class IfcRelAssignsToGroup(IfcRelationship):
    pass


# Properties


class IfcProperty(IfcRoot):
    pass


class IfcPropertySingleValue(IfcProperty):
    pass


class IfcPropertySet(IfcBaseType):
    pass


class IfcRelDefinesByProperties(IfcRelationship):
    pass


# Quantities


class IfcElementQuantity(IfcPropertySet):
    pass


class IfcPhysicalSimpleQuantity(IfcBaseType):
    pass


class IfcQuantityLength(IfcPhysicalSimpleQuantity):
    pass


class IfcQuantityArea(IfcPhysicalSimpleQuantity):
    pass


class IfcQuantityVolume(IfcPhysicalSimpleQuantity):
    pass


class IfcQuantityMass(IfcPhysicalSimpleQuantity):
    pass


# Materials


class IfcMaterial(IfcBaseType):
    pass


class IfcMaterialLayer(IfcBaseType):
    pass


class IfcMaterialLayerSet(IfcBaseType):
    pass


class IfcMaterialLayerSetUsage(IfcBaseType):
    pass


class IfcRelAssociatesMaterial(IfcRelationship):
    pass


# Simple Values


class IfcSimpleValue(IfcBaseType):
    pass


class IfcInteger(IfcSimpleValue):
    pass


class IfcText(IfcSimpleValue):
    pass


class IfcBoolean(IfcSimpleValue):
    pass


# Others


class IfcRelAggregates(IfcRelationship):
    pass


class IfcSIUnit(IfcBaseType):
    pass


class IfcOwnerHistory(IfcBaseType):
    pass


# Geometry


class IfcShapeRepresentation(IfcBaseType):
    pass


class IfcRepresentationMap(IfcBaseType):
    pass


# Models


class IfcGeometricRepresentationItem(IfcBaseType):
    pass


class IfcFaceBasedSurfaceModel(IfcGeometricRepresentationItem):
    pass


class IfcSolidModel(IfcGeometricRepresentationItem):
    pass


class IfcExtrudedAreaSolid(IfcSolidModel):
    pass


class IfcCurve(IfcGeometricRepresentationItem):
    pass


class IfcPolyline(IfcCurve):
    pass


class IfcMappedItem(IfcGeometricRepresentationItem):
    pass


class IfcPlacement(IfcGeometricRepresentationItem):
    pass


class IfcAxis1Placement(IfcPlacement):
    pass


class IfcAxis2Placement2d(IfcPlacement):
    pass


class IfcAxis2Placement3d(IfcPlacement):
    pass


class IfcCartesianTransformationOperator3dNonUniform(IfcGeometricRepresentationItem):
    pass


class IfcDirection(IfcGeometricRepresentationItem):
    pass


class IfcCartesianPoint(IfcGeometricRepresentationItem):
    pass


# Topology


class IfcTopologicalRepresentationItem(IfcBaseType):
    pass


class IfcPolyLoop(IfcTopologicalRepresentationItem):
    pass


class IfcFaceOuterBound(IfcTopologicalRepresentationItem):
    pass


class IfcFace(IfcTopologicalRepresentationItem):
    pass


class IfcConnectedFaceSet(IfcTopologicalRepresentationItem):
    pass


# ProfileDef


class IfcProfileDef(IfcBaseType):
    pass


class IfcArbitraryClosedProfileDef(IfcProfileDef):
    pass


class IfcArbitraryProfileDefWithVoids(IfcArbitraryClosedProfileDef):
    pass


# Others


class IfcProductDefinitionShape(IfcBaseType):
    pass


class IfcRepresentationContext(IfcBaseType):
    pass


class IfcProject(IfcBaseType):
    pass


# Placement


class IfcObjectPlacement(IfcBaseType):
    pass


class IfcLocalPlacement(IfcObjectPlacement):
    pass
