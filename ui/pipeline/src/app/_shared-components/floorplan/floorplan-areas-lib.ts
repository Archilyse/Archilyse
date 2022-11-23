import { EditorConstants } from '../../_shared-libraries/EditorConstants';
import { FloorplanEditorComponent } from './floorplan-editor.component';

import { MeshPhongMaterial } from 'three-full/builds/Three.es.js';
import { BrooksHelper } from '../../_shared-libraries/BrooksHelper';

/** Color when clicked */
const colorClick = 0x99ff;

export class FloorplanAreasLib {
  /**
   * When color indexes are provided (to color referenced areas)
   * This function returns the right color for each areaId
   * @param colorIndexes
   * @param areaId
   */
  public static getColor(colorIndexes, areaId) {
    if (colorIndexes?.[areaId]) {
      return colorIndexes[areaId];
    }
    return '#898989'; // '#ECECEC';
  }

  /**
   * User mouses over a material we highlight it
   * @param component
   * @param event
   * @param material
   * @param color
   * @param objectData
   */
  public static mouseOverMaterial(component: FloorplanEditorComponent, event, material, color, objectData) {
    let mouseOver = false;

    if (objectData) {
      // Mouse over highlight
      FloorplanAreasLib.highlightMaterialOver(component, material);
      mouseOver = true;
    }

    if (!mouseOver) {
      document.body.style.cursor = 'default';
      FloorplanAreasLib.restoreMaterialOver(component, material);
    }
  }

  /**
   * Given a threeJs representation of an area,
   * and it's updated data we redraw it if necessary
   * @param component
   * @param material
   * @param objectData
   * @param floorNr
   */
  public static redrawArea(component: FloorplanEditorComponent, material, objectData, floorNr) {
    const logic = component.logic;
    FloorplanAreasLib.restoreMaterialOver(component, null);
    const containerSpace = material && material.parent && material.parent.parent;
    if (containerSpace) {
      containerSpace.remove(material.parent);
      delete logic.uuidToObject[material.uuid];
      component.analyzeStructure(containerSpace, objectData, 1, floorNr, false);
    }
    component.calculateObjectsToIntersectDelayed();
    component.render();
  }

  /**
   * We change the threejs material to fit the given type if they are different
   * @param component
   * @param material
   * @param element
   * @param oldType
   * @param newType
   */
  public static changeApartmentType(component: FloorplanEditorComponent, material, element, oldType, newType) {
    if (oldType !== newType) {
      // Change type
      element.type = newType;

      const newTypeShort = BrooksHelper.getHumanType(newType);

      component.areaService.setAreaType(element.floorNr, element.id, newTypeShort);
      component.editorService.changedType(element, oldType, newType);
      FloorplanAreasLib.redrawArea(component, material, element, EditorConstants.DEFAULT_FLOOR);

      component.render();
    }
  }

  /**
   * We change the material appearance when we select it
   * @param component
   * @param mesh
   */
  public static highlightMaterial(component: FloorplanEditorComponent, mesh) {
    component.logic.highlightMaterial(component, mesh);
    return true;
  }

  public static highlightMaterialLogic(component: FloorplanEditorComponent, mesh) {
    FloorplanAreasLib.restoreMaterial(component);

    if (component.previousMesh !== null && component.previousMesh.uuid === mesh.uuid) {
      component.render();
      return false;
    }

    const material = new MeshPhongMaterial({
      color: colorClick,
      emissive: colorClick,
      transparent: true,
      opacity: 0.5,
    });

    if (component.previousMeshOver !== null && component.previousMeshOver.uuid === mesh.uuid) {
      component.previousMeshMaterial = component.previousMeshOverMaterial;
    } else {
      component.previousMeshMaterial = mesh.material;
    }

    component.previousMesh = mesh;
    mesh.material = material;
    component.render();
  }

  /**
   * We change the material properties when we mouse over it
   * @param component
   * @param mesh
   */
  public static highlightMaterialOver(component: FloorplanEditorComponent, mesh) {
    if (!FloorplanAreasLib.restoreMaterialOver(component, mesh)) {
      return false;
    }

    if (component.previousMeshOver !== null && component.previousMeshOver.uuid === mesh.uuid) {
      component.previousMeshOver = null;
    } else if (component.previousMesh !== null && component.previousMesh.uuid === mesh.uuid) {
      // Do nothing
    } else if (mesh.material) {
      const result = component.logic.highlightMaterialOver(component, mesh);

      mesh.material = new MeshPhongMaterial({
        color: result.newColor,
        emissive: result.newColor,
        transparent: true,
        opacity: result.newOpacity,
      });
    }
  }

  /**
   * After selecting a material we restore the original color
   */
  public static restoreMaterial(component: FloorplanEditorComponent) {
    component.logic.restoreMaterial(component);
  }

  /**
   * After mouse over we restore the original color
   * @param component
   * @param newMesh
   */
  public static restoreMaterialOver(component: FloorplanEditorComponent, newMesh) {
    if (component.previousMeshOver !== null) {
      component.logic.restoreMaterialOver(component, newMesh);

      // Skip when the second mouse over reached the same polygon
      if (newMesh !== null && component.previousMeshOver.uuid === newMesh.uuid) {
        return false;
      }

      // No restore when was clicked
      if (component.previousMesh !== null && component.previousMesh.uuid === component.previousMeshOver.uuid) {
        component.previousMeshOver = null;
        return false;
      }

      if (component.previousMeshOverMaterial) {
        component.previousMeshOver.material = component.previousMeshOverMaterial;
      }

      component.previousMeshOver = null;

      component.render();
    }
    return true;
  }
}
