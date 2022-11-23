import { EditorConstants } from '../../_shared-libraries/EditorConstants';
import { FloorplanInterfaceService } from './floorplan.interface.service';

export class FloorplanIdManager {
  /**
   * Re recover the original model_structure object from the scene element
   * @param logic implements FloorplanInterfaceService
   * @param mesh
   */
  public static getMeshObjectData(logic: FloorplanInterfaceService, mesh) {
    if (logic) {
      return logic.uuidToObject[mesh.uuid];
    }
    return null;
  }

  /**
   * Given the brooks Id we get the corresponding mesh
   * @param logic implements FloorplanInterfaceService
   * @param id The brooks Id
   */
  public static getMeshById(logic: FloorplanInterfaceService, id) {
    if (logic?.idToObject[id]) {
      return logic.idToObject[id];
    }
    return null;
  }

  /**
   * Given the index of an error element it returns that element
   * @param logic
   * @param index
   */
  public static getErrorByIndex(logic: FloorplanInterfaceService, index) {
    if (logic?.indexToError) {
      return logic.indexToError[index];
    }
    return null;
  }

  /**
   * Standard identifier for an area.
   * Requires disambiguation by floor because the same plan might be used in different floor
   * @param areaId
   * @param floorNr
   */
  public static getAreaId(areaId, floorNr) {
    return `${floorNr}:${areaId}`;
  }

  public static getAreaByIdAndFloorNr(logic: FloorplanInterfaceService, areaId, floorNr) {
    if (logic) {
      return logic.idAndFloorToArea[this.getAreaId(areaId, floorNr)];
    }
    return null;
  }

  public static getUnitById(logic: FloorplanInterfaceService, unitId) {
    if (logic) {
      return logic.idToUnit[`${unitId}`];
    }
    return null;
  }

  /**
   * We remove the object dictionary to re render again
   * @param logic implements FloorplanInterfaceService
   */
  public static cleanRegisteredObjects(logic: FloorplanInterfaceService) {
    if (logic) {
      logic.uuidToObject = {};
      logic.idToObject = {};
      logic.idAndFloorToArea = {};
      logic.idToUnit = {};
      logic.indexToError = {};
    }
  }

  /**
   * We register the error mesh elements to be able to identify and modify them (to highlight)
   * @param logic
   * @param mesh
   * @param index
   */
  public static registerError(logic: FloorplanInterfaceService, mesh, index) {
    if (logic) {
      logic.indexToError[index] = mesh;
    }
  }

  /**
   * We register a pair (scene elemenet) <-> (model_structure object)
   * @param logic implements FloorplanInterfaceService
   * @param mesh
   * @param objectClass
   * @param object
   */
  public static registerObject(logic: FloorplanInterfaceService, mesh, objectClass, object) {
    if (logic) {
      if (!logic.uuidToObject) {
        this.cleanRegisteredObjects(logic);
      }

      logic.uuidToObject[mesh.uuid] = {
        group: objectClass,
        data: object,
      };

      if (objectClass === EditorConstants.UNIT) {
        logic.idToObject[object.object.id] = mesh;
        logic.idToUnit[`${object.object.unitId}`] = mesh;
      } else if (objectClass === EditorConstants.AREA) {
        logic.idToObject[object.object.id] = mesh;
        logic.idAndFloorToArea[this.getAreaId(object.object.id, object.object.floorNr)] = mesh;
      }
    }
  }
}
