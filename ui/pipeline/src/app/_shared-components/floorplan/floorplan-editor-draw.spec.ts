import { FloorplanEditorDraw } from './floorplan-editor-draw';
import { EditorConstants } from '../../_shared-libraries/EditorConstants';
import { COOR_X, COOR_Y } from '../../_shared-libraries/SimData';
import { FloorplanClassificationService } from '../../_services/floorplan/floorplan.classification.service';
import { FloorplanIdManager } from '../../_services/floorplan/floorplanIdManager';

/**
 * Helping class that mocks the threeJs scene
 */
let _addedElements = 0;
const buildingStructureMock = {
  add: () => {
    _addedElements += 1;
  },

  /** Only for testing purposes */
  _reset: () => {
    _addedElements = 0;
  },
  _get: () => {
    return _addedElements;
  },
};

/**
 * Example object to draw
 */
const exampleObjectToDraw = {
  type: EditorConstants.DESK,
  dim: [2, 2],
  position: {
    coordinates: [1, 1],
  },
};

const logic = new FloorplanClassificationService();

describe('Floorplan editor drawing library', () => {
  beforeEach(() => {
    buildingStructureMock._reset();

    // By default we clean the registered objects
    FloorplanIdManager.cleanRegisteredObjects(logic);
  });

  it('should draw a window in the scene', () => {
    const register = true; // We'll register the element

    const objectType = EditorConstants.WINDOW;
    const originalWindowObject = {
      footprint: {
        type: 'Polygon',
        coordinates: [
          [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1],
            [0, 0],
          ],
        ],
      },
      position: {
        coordinates: [1, 1],
      },
      angle: 0,
    };

    FloorplanEditorDraw.drawWindows(register, null, buildingStructureMock, objectType, originalWindowObject);

    expect(buildingStructureMock._get()).toBe(1);
  });

  it('should  draw a door opening in the scene', () => {
    const doorLength = 1;
    const opening_area = {
      open: [0, doorLength],
      axis: [0, 0],
      close: [doorLength, 0],
    };

    FloorplanEditorDraw.drawOpenings(buildingStructureMock, opening_area);

    expect(buildingStructureMock._get()).toBe(1);
  });

  it('should draw a door in the scene', () => {
    const polygon = {
      type: 'Polygon',
      coordinates: [
        [
          [0, 0],
          [1, 0],
          [0, 1],
          [0, 0],
        ],
        [
          [2, 2],
          [1, 0],
          [0, 1],
          [2, 2],
        ],
      ],
    };

    FloorplanEditorDraw.drawDoors(buildingStructureMock, polygon);
    expect(buildingStructureMock._get()).toBe(2);
  });

  it('should draw a line in the scene', () => {
    const polygon = {
      type: 'Polygon',
      coordinates: [
        [
          [0, -1],
          [1, 0],
          [0, 1],
          [0, -1],
        ],
        [
          [2, 2],
          [1, 0],
          [0, 1],
          [2, 2],
        ],
      ],
    };
    FloorplanEditorDraw.drawLines(buildingStructureMock, polygon);
    expect(buildingStructureMock._get()).toBe(2);
  });

  it('should draw a generic fixture element', () => {
    const register = true; // We'll register the element
    const areaService = null;
    FloorplanEditorDraw.drawGenericElement(register, areaService, buildingStructureMock, exampleObjectToDraw);

    expect(buildingStructureMock._get()).toBe(1);
  });

  it('should draw and register an generic polygon', () => {
    const register = true; // We'll register the element

    const data = {
      type: 'Polygon',
      coordinates: [
        [
          [0, -1],
          [1, 0],
          [0, 1],
          [0, -1],
        ],
      ],
    };

    FloorplanEditorDraw.drawGenericsPolygon(register, null, buildingStructureMock, exampleObjectToDraw, data);

    expect(buildingStructureMock._get()).toBe(1);
  });

  it('should center an object in the scene', () => {
    let changedX = null;
    let changedY = null;

    const objectGroup = {
      translateX: newX => {
        changedX = newX;
      },
      translateY: newY => {
        changedY = newY;
      },
      rotation: {
        z: 0,
      },
    };
    const position = [5, 10];

    FloorplanEditorDraw.centerObject(objectGroup, position);

    expect(changedX).toBe(position[COOR_X]);
    expect(changedY).toBe(position[COOR_Y]);
  });

  it('should register a threeJs object to be recover after', () => {
    const exampleObjectId = 'objectId';
    const exampleUuid = 'example-uuid-unique-identifier';

    const mesh = {
      uuid: exampleUuid,
    };
    const objectClass = 'AREA';
    const object = {
      object: {
        id: exampleObjectId,
        floorNr: EditorConstants.DEFAULT_FLOOR,
      },
    };

    // We register the object and we recover the data
    FloorplanIdManager.registerObject(logic, mesh, objectClass, object);
    const recoveredMesh = FloorplanIdManager.getMeshById(logic, exampleObjectId);

    // We check the recovered data
    expect(recoveredMesh).not.toBeNull();
    expect(recoveredMesh.uuid).toBe(exampleUuid);

    // We recover the object data our of the mesh
    const recoveredObjectData = FloorplanIdManager.getMeshObjectData(logic, recoveredMesh);

    expect(recoveredObjectData).not.toBeNull();
    expect(recoveredObjectData.group).toBe(objectClass);
    expect(recoveredObjectData.data.object.id).toBe(exampleObjectId);

    // We clean the objects and we check if they are null
    FloorplanIdManager.cleanRegisteredObjects(logic);
    const recoveredMeshNull = FloorplanIdManager.getMeshById(logic, exampleObjectId);
    expect(recoveredMeshNull).toBeNull();
  });
});
