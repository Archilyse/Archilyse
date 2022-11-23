import { FloorplanUnitsLib } from './floorplan-units-lib';
import { EditorConstants } from '../../_shared-libraries/EditorConstants';
import { EditorMath } from '../../_shared-libraries/EditorMath';
import { FloorplanAreasLib } from './floorplan-areas-lib';
import { FloorplanEditorLib } from './floorplan-editor-lib';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { Raycaster, Vector2 } from 'three-full/builds/Three.es.js';
import { FloorplanIdManager } from '../../_services/floorplan/floorplanIdManager';

/**
 * Function cannot be called again if delay ms didn't pass
 * @param delay
 * @param fn
 */
function debounce(delay, fn) {
  let timerId;
  return function (...args) {
    if (timerId) {
      clearTimeout(timerId);
    }
    timerId = setTimeout(() => {
      fn(...args);
      timerId = null;
    }, delay);
  };
}

/**
 * Class to handle the mouse events over the floorplan
 */
export class FloorplanMouseLib {
  public static setUpMouseEvents(component: FloorplanEditorComponent) {
    // No more than 10 mouse moves pro sec
    component.mousemoveListener = debounce(100, FloorplanMouseLib.onMouseMove.bind(component, component));

    component.mouseoutListener = FloorplanMouseLib.onMouseOut.bind(component, component);
    component.mousedownListener = FloorplanMouseLib.onMouseClick.bind(component, component);
    component.mouseupListener = FloorplanMouseLib.onMouseUp.bind(component, component);

    component.container.addEventListener('mousemove', component.mousemoveListener, false);
    component.container.addEventListener('mouseout', component.mouseoutListener, false);
    component.container.addEventListener('mousedown', component.mousedownListener, false);
    component.container.addEventListener('mouseup', component.mouseupListener, false);

    component.raycaster = new Raycaster(null, null, Number.MIN_SAFE_INTEGER, Number.MAX_SAFE_INTEGER);
    component.mouse = new Vector2();
  }

  public static onMouseUpdate(component: FloorplanEditorComponent, event) {
    FloorplanMouseLib.updateMouse(component, event);
    const rayCaster = new Raycaster();
    rayCaster.setFromCamera(component.mouse, component.camera);
    rayCaster.near = Number.MIN_SAFE_INTEGER;
    rayCaster.far = Number.MAX_SAFE_INTEGER;

    return rayCaster;
  }

  public static onMouseMove(component: FloorplanEditorComponent, event) {
    const rayCaster = FloorplanMouseLib.onMouseUpdate(component, event);
    // calculate objects intersecting the picking ray
    FloorplanMouseLib.identifyMaterial(
      component,
      event,
      rayCaster.intersectObjects(component.objectsToIntersect),
      0x00ff00
    );
  }

  public static onMouseClick(component: FloorplanEditorComponent, event) {
    const rayCaster = FloorplanMouseLib.onMouseUpdate(component, event);

    // Only left click has to be evaluated
    if (event.button === 0) {
      // calculate objects intersecting the picking ray
      FloorplanMouseLib.identifyMaterial(
        component,
        event,
        rayCaster.intersectObjects(component.objectsToIntersect),
        0xff0000
      );
    }
  }

  public static onMouseUp(component: FloorplanEditorComponent, event) {
    FloorplanMouseLib.onMouseUpdate(component, event);
  }

  public static updateMouseGeneral(component: FloorplanEditorComponent, eventX, eventY) {
    FloorplanEditorLib.updateComponentCoordinates(component);
    component.mouse.x = ((eventX - component.left) / component.width) * 2 - 1;
    component.mouse.y = (-(eventY - component.top) / component.height) * 2 + 1;
  }
  public static updateMouse(component: FloorplanEditorComponent, event) {
    event.preventDefault();
    FloorplanMouseLib.updateMouseGeneral(component, event.clientX, event.clientY);
  }

  public static onMouseOut(component: FloorplanEditorComponent, event) {
    document.body.style.cursor = 'default';
    FloorplanMouseLib.onMouseUpdate(component, event);
  }

  /**
   * We raytrace the mouse to identify the element depending on the type of event
   * @param component
   * @param event
   * @param intersects
   * @param color
   */
  public static identifyMaterial(component: FloorplanEditorComponent, event, intersects, color) {
    const logic = component.logic;
    if (intersects.length) {
      const filtered = intersects.filter(o => o.object.type === EditorConstants.THREEJS_MESH);
      const isAClick = (event.type === 'click' || event.type === 'mousedown') && event.button === 0;
      // It's a mesh
      if (filtered.length) {
        // First element selected by default.
        let mesh;
        let objectData;
        let surface = Number.MAX_SAFE_INTEGER;

        for (let i = filtered.length - 1; i >= 0; i -= 1) {
          const meshFound = filtered[i].object;
          const objectDataFound = FloorplanIdManager.getMeshObjectData(logic, meshFound);
          let addObject = false;
          if (
            objectDataFound &&
            ((objectDataFound.data && objectDataFound.data.areaData) ||
              (objectDataFound.group && objectDataFound.group === EditorConstants.UNIT))
          ) {
            addObject = true;

            // Smallest area goes first in case of areas overlapping
            const areaSurface = EditorMath.calculateAreaFromPolygon(objectDataFound.data.areaData);

            if (areaSurface < surface) {
              surface = areaSurface;
            } else {
              addObject = false;
            }
          }
          if (addObject) {
            mesh = meshFound;
            objectData = objectDataFound;
          }
        }

        if (objectData && (objectData.group === EditorConstants.AREA || objectData.group === EditorConstants.UNIT)) {
          if (event.type === 'mousemove') {
            if (logic.highlightUnits) {
              FloorplanUnitsLib.restoreUnitMaterialOver(component.selectedMeshes, component.previousMaterials);
              const floorNr = EditorConstants.DEFAULT_FLOOR;
              FloorplanUnitsLib.highlightUnitAsAreas(component, objectData.data.object.sel_apartment, floorNr);
            } else {
              FloorplanAreasLib.mouseOverMaterial(component, event, mesh, color, objectData);
            }
            component.forceRender();

            // Only when the left button (button 0) is clicked
          } else if (isAClick) {
            this.clickMaterial(component, event, mesh, color, objectData);
          } else {
            console.error('Event event.type: ', event.type, event.button);
          }
        }

        return;
      }
    }

    if (event.type === 'mousemove') {
      if (!intersects.length) {
        FloorplanAreasLib.restoreMaterialOver(component, null);
        if (logic.highlightUnits) {
          FloorplanUnitsLib.restoreUnitMaterialOver(component.selectedMeshes, component.previousMaterials);
          component.forceRender();
        }
      }
    } else if (event.type === 'click' || event.type === 'mousedown') {
      FloorplanAreasLib.restoreMaterial(component);
    }
  }

  /**
   * User clicks in a material
   * We select it and show properties in the sidebar
   * @param component
   * @param event
   * @param mesh
   * @param color
   * @param objectData
   */
  public static clickMaterial(component: FloorplanEditorComponent, event, mesh, color, objectData) {
    const logic = component.logic;
    if (objectData && objectData.group === EditorConstants.AREA) {
      logic.clickMaterialArea(component, event, mesh, color, objectData);
      const deselect = objectData.group === 'Unknown element';

      if (deselect) {
        FloorplanAreasLib.restoreMaterial(component);
      } else {
        FloorplanAreasLib.highlightMaterial(component, mesh);
      }
    } else if (objectData && objectData.group === EditorConstants.UNIT) {
      FloorplanUnitsLib.highlightUnit(component, mesh);
    } else {
      FloorplanAreasLib.restoreMaterial(component);
    }
  }
}
