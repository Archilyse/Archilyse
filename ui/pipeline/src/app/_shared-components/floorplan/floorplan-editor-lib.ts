import { Box3, BoxGeometry, Mesh, MeshBasicMaterial, Vector3 } from 'three-full/builds/Three.es.js';
import { EditorConstants, isASeparator, isAnArea } from '../../_shared-libraries/EditorConstants';

import { FloorplanEditorComponent } from './floorplan-editor.component';

export class FloorplanEditorLib {
  /**
   * Creates a list of objects that are visible in the scene.
   * if "onlyAreasOrWalls" is true takes in consideration those who are Areas or Separators
   * @param objectsInitial, objects that we have already in the list.
   * @param group
   * @param onlyAreasOrWalls
   */
  public static concatIfVisibleGroupOfGroups(objectsInitial, group, onlyAreasOrWalls) {
    let objects = objectsInitial;

    if (group.visible) {
      const meshes = [];
      group.children.forEach(child => {
        if (child.type === EditorConstants.THREEJS_GROUP) {
          objects = FloorplanEditorLib.concatIfVisibleGroupOfGroups(objects, child, onlyAreasOrWalls);
        } else if (child.type === EditorConstants.THREEJS_MESH) {
          if (onlyAreasOrWalls) {
            if (
              child.parent &&
              child.parent.userData &&
              (isAnArea(child.parent.userData.type) || isASeparator(child.parent.userData.type))
            ) {
              meshes.push(child);
            }
          } else {
            meshes.push(child);
          }
        }
      });

      return [...objects, ...meshes];
    }
    return objects;
  }

  /**
   * If the conponent got the property backgroundImg loads the given image.
   * backgroundImgWidth and backgroundImgHeight are needed too.
   * @param component
   */
  public static loadBackgroundImg(component: FloorplanEditorComponent) {
    if (component.backgroundImg) {
      const geometry = new BoxGeometry(component.backgroundImgWidth, component.backgroundImgHeight, 0);
      const material_1 = new MeshBasicMaterial({
        map: component.backgroundImg,
        transparent: true,
      });

      const cube = new Mesh(geometry, material_1);
      this.transformMesh(cube, component);

      component.backgroundImgElement = cube;
      component.scene.add(cube);
    }
  }
  /**
   * The mesh (background image) needs to be shifted, scaled & rotated the same way as the user did
   * in the react editor. Otherwise the brooks model is not correctly matching with the background image.
   */
  public static transformMesh(mesh: Mesh, component: FloorplanEditorComponent) {
    mesh.position.x = component.backgroundImgWidth * 0.5 * component.backgroundImgScale + component.backgroundImgShiftX;
    mesh.position.y =
      component.backgroundImgHeight * 0.5 * component.backgroundImgScale + component.backgroundImgShiftY;
    mesh.position.z = -10;
    mesh.scale.setX(component.backgroundImgScale);
    mesh.scale.setY(component.backgroundImgScale);
    mesh.rotateZ((-component.backgroundImgRotation * 2 * Math.PI) / 360);
  }

  /**
   * Container bounding box calculation
   */
  public static updateComponentCoordinates(component: FloorplanEditorComponent) {
    const rect = component.container.getBoundingClientRect();
    const rectBody = document.body.getBoundingClientRect();

    component.top = rect.top - rectBody.top;
    component.left = rect.left - rectBody.left;

    component.width = component.container.offsetWidth;
    component.height = component.container.offsetHeight;
  }

  /**
   * Gets the properties of the scene displayed
   */
  public static containerProps(component: FloorplanEditorComponent) {
    FloorplanEditorLib.updateComponentCoordinates(component);

    let geometryWidth = 1;
    let geometryHeight = 1;

    const sceneBBox = new Box3().setFromObject(component.scene);
    if (sceneBBox && sceneBBox.max && sceneBBox.min) {
      geometryWidth = sceneBBox.max.x - sceneBBox.min.x;
      geometryHeight = sceneBBox.max.y - sceneBBox.min.y;
    }

    const rationScreen = component.width / component.height;
    const rationModel = geometryWidth / geometryHeight;

    const halfGeometryWidth = geometryWidth / 2;
    const halfGeometryHeight = geometryHeight / 2;

    if (rationScreen > rationModel) {
      return {
        left: -halfGeometryHeight * rationScreen,
        right: halfGeometryHeight * rationScreen,
        top: halfGeometryHeight,
        bottom: -halfGeometryHeight,
      };
    }

    return {
      left: -halfGeometryWidth,
      right: halfGeometryWidth,
      top: halfGeometryWidth / rationScreen,
      bottom: -halfGeometryWidth / rationScreen,
    };
  }
}
