import { EditorConstants, isASpace, isFurniture } from '../../_shared-libraries/EditorConstants';
import { Group } from 'three-full/builds/Three.es';
import { EditorMath } from '../../_shared-libraries/EditorMath';
import { COOR_X, COOR_Y } from '../../_shared-libraries/SimData';
import { drawGeometries, drawPolygons, drawText } from '../../_shared-libraries/Geometries';
import { EditorCoordinates } from '../../_shared-libraries/EditorCoordinates';
import { FloorplanIdManager } from '../../_services/floorplan/floorplanIdManager';

/** Base Layer */
const LAYER_1 = 0.4;
/** 2nd Layer */
const LAYER_2 = 0.8;
/** 3rd Layer */
const LAYER_3 = 1.2;
/** 4th Layer */
const LAYER_4 = 1.6;

export class FloorplanEditorDraw {
  /**
   * Draw windows with line in the middle.
   * @param register
   * @param areaService
   * @param buildingStructure
   * @param objectType
   * @param originalObject
   */
  public static drawWindows(register, areaService, buildingStructure, objectType, originalObject) {
    const objectGroup = new Group();
    objectGroup.userData = originalObject;
    buildingStructure.add(objectGroup);

    const coordinatesLine = [];

    const coordinates = originalObject.footprint.coordinates[0];

    const lD1 = EditorMath.distance(
      coordinates[0][COOR_X],
      coordinates[0][COOR_Y],
      coordinates[1][COOR_X],
      coordinates[1][COOR_Y]
    );
    const lD2 = EditorMath.distance(
      coordinates[1][COOR_X],
      coordinates[1][COOR_Y],
      coordinates[2][COOR_X],
      coordinates[2][COOR_Y]
    );

    if (lD2 > lD1) {
      const middleX = (coordinates[1][COOR_X] + coordinates[0][COOR_X]) / 2;
      const middleY = (coordinates[1][COOR_Y] + coordinates[0][COOR_Y]) / 2;

      const middle2X = (coordinates[3][COOR_X] + coordinates[2][COOR_X]) / 2;
      const middle2Y = (coordinates[3][COOR_Y] + coordinates[2][COOR_Y]) / 2;

      coordinatesLine.push([middleX, middleY]);
      coordinatesLine.push([middle2X, middle2Y]);
    } else {
      const middleX = (coordinates[2][COOR_X] + coordinates[1][COOR_X]) / 2;
      const middleY = (coordinates[2][COOR_Y] + coordinates[1][COOR_Y]) / 2;

      const middle2X = (coordinates[4][COOR_X] + coordinates[3][COOR_X]) / 2;
      const middle2Y = (coordinates[4][COOR_Y] + coordinates[3][COOR_Y]) / 2;

      coordinatesLine.push([middleX, middleY]);
      coordinatesLine.push([middle2X, middle2Y]);
    }

    this.drawLines(objectGroup, originalObject.footprint);

    this.drawPolygonsAndRegister(
      register,
      objectGroup, // buildingStructure,
      areaService,
      null,
      1,
      originalObject,
      objectType,
      originalObject.footprint,
      0xffffff,
      null,
      LAYER_4,
      null
    );

    this.drawLines(objectGroup, {
      type: 'Polygon',
      coordinates: [coordinatesLine],
    });

    return this.centerObject(objectGroup, originalObject.position.coordinates);
  }

  /**
   * Calculate door openings
   * @param buildingStructure
   * @param opening_area
   */
  public static drawOpenings(buildingStructure, opening_area) {
    const points = EditorMath.calculateDoorOpenings(opening_area);
    drawGeometries(
      buildingStructure,
      {
        type: 'Polygon',
        coordinates: [points],
      },
      0x333333,
      1.5,
      LAYER_1
    );
    return points;
  }

  public static drawDoors(parentStructure, footprint) {
    // drawGeometries(buildingStructure, data, 0x333333, 1.5, LAYER_1);
    drawGeometries(
      parentStructure, // buildingStructure
      footprint,
      0x333333,
      1.5,
      LAYER_4
    );

    return parentStructure;
  }

  public static drawLines(buildingStructure, polygon) {
    drawGeometries(buildingStructure, polygon, 0x0, 1, LAYER_3);
  }

  public static drawGenericElement(register, areaService, objectPolygons, originalObject) {
    let footprint;

    if (originalObject) {
      if (originalObject.dim) {
        const dX = originalObject.dim[COOR_X];
        const dY = originalObject.dim[COOR_Y];

        footprint = {
          type: 'Polygon',
          coordinates: [EditorCoordinates.rectangle(dX, dY)],
        };
      } else if (originalObject.footprint) {
        footprint = originalObject.footprint;
      } else {
        console.error('originalObject without dimensions or footprint');
      }

      return this.drawGenericsPolygon(register, areaService, objectPolygons, originalObject, footprint);
    }

    console.error('originalObject not defined');
  }

  /**
   * Method to draw standard elements from the model_structure
   * @param register
   * @param areaService
   * @param deskPolygons
   * @param originalObject
   * @param polygon
   */
  public static drawGenericsPolygon(register, areaService, deskPolygons, originalObject, polygon) {
    let objectClass;
    let zDiff = 0;

    if (isFurniture(originalObject.type)) {
      objectClass = originalObject.type;
      if (originalObject.type === EditorConstants.DESK) {
        zDiff = 0.2;
      } else if (originalObject.type === EditorConstants.CHAIR) {
        zDiff = 0.1;
      }
    } else {
      console.error('Unknown Object type', originalObject, originalObject.type);
    }

    const objectGroup = new Group();

    drawGeometries(objectGroup, polygon, 0x0, 1, LAYER_2 + zDiff);

    this.drawPolygonsAndRegister(
      register,
      objectGroup,
      areaService,
      null,
      1,
      originalObject,
      objectClass,
      polygon,
      0xffffff,
      null,
      LAYER_2 + zDiff,
      null,
      0.8
    );

    objectGroup.userData = originalObject;
    deskPolygons.add(objectGroup);

    return this.centerObject(objectGroup, originalObject.position.coordinates);
  }

  /**
   * Method to draw AREAS from the model structure
   * @param register
   * @param areaService
   * @param editorLogic
   * @param editorScale
   * @param areaPolygons
   * @param originalObject
   * @param fillAreaColors
   * @param fontThree
   * @param position
   * @param polygon
   * @param index
   */
  public static drawAreas(
    register,
    areaService,
    editorLogic,
    editorScale,
    areaPolygons,
    originalObject,
    fillAreaColors,
    fontThree,
    position,
    polygon,
    index
  ) {
    // Hidden by default

    // NO REGISTER:
    // drawPolygons(areaPolygons,AREA,data,fillAreaColors,LAYER_1,null,0.6,() => {});
    const objectGroup = new Group();

    // Spaces are transparent
    if (!isASpace(originalObject.type)) {
      this.drawPolygonsAndRegister(
        register,
        objectGroup, // areaPolygons,
        areaService,
        editorLogic,
        editorScale,
        originalObject,
        EditorConstants.AREA,
        polygon,
        fillAreaColors,
        fontThree,
        -LAYER_1 + index / 10,
        null,
        0.6
      );
    }
    objectGroup.userData = originalObject;
    areaPolygons.add(objectGroup);

    return this.centerObject(objectGroup, position);
  }

  /**
   * Method to draw WALLS from the model structure
   * @param register
   * @param areaService
   * @param editorLogic
   * @param parentStructure
   * @param originalObject
   * @param objectType
   * @param position
   * @param wallPolygon
   */
  public static drawWalls(
    register,
    areaService,
    editorLogic,
    parentStructure,
    originalObject,
    objectType,
    position,
    wallPolygon
  ) {
    const objectGroup = new Group();

    this.drawPolygonsAndRegister(
      register,
      objectGroup,
      areaService,
      editorLogic,
      1,
      originalObject,
      objectType,
      wallPolygon,
      0x0,
      null,
      LAYER_3
    );

    objectGroup.userData = originalObject;
    parentStructure.add(objectGroup);

    return this.centerObject(objectGroup, position);
  }

  public static centerObject(objectGroup, position) {
    objectGroup.translateX(position[COOR_X]);
    objectGroup.translateY(position[COOR_Y]);
    return objectGroup;
  }

  public static drawPolygonsAndRegister(
    register,
    container,
    areaService,
    editorLogic,
    editorScale,
    originalObject,
    objectClass,
    polygon,
    materialColor,
    fontThree,
    zIndex,
    forceMaterial = null,
    polygonOpacity = 1
  ) {
    drawPolygons(
      container,
      areaService,
      editorLogic,
      editorScale,
      originalObject,
      objectClass,
      polygon,
      materialColor,
      fontThree,
      zIndex,
      forceMaterial,
      polygonOpacity,
      (segmentMesh, objectClass, i) => {
        let object;
        if (objectClass === EditorConstants.CHAIR) {
          object = {
            seatIndex: i,
            object: originalObject,
          };
        } else if (objectClass === EditorConstants.DESK) {
          const seatsGeometries = null;
          object = {
            deskData: polygon,
            seats: seatsGeometries,
            object: originalObject,
          };
        } else if (
          objectClass === EditorConstants.TOILET ||
          objectClass === EditorConstants.ELEVATOR ||
          objectClass === EditorConstants.KITCHEN ||
          objectClass === EditorConstants.OFFICE_MISC
        ) {
          object = {
            object: originalObject,
          };
        } else if (objectClass === EditorConstants.DOOR || objectClass === EditorConstants.ENTRANCE_DOOR) {
          object = {
            object: originalObject,
          };
        } else if (objectClass === EditorConstants.AREA) {
          object = {
            areaIndex: i,
            areaData: polygon,
            object: originalObject,
          };
        } else {
          object = {
            object: originalObject,
          };
        }

        if (register) {
          FloorplanIdManager.registerObject(editorLogic, segmentMesh, objectClass, object);
        }
      }
    );
  }

  public static drawText(text, group, fontThree, areaSurface) {
    drawText(text, group, fontThree, areaSurface, LAYER_4);
  }
}
