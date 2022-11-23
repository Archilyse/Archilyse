import { FloorplanEditorComponent } from './floorplan-editor.component';
import { FloorplanEditorLib } from './floorplan-editor-lib';
import { OrthographicCamera, OrbitControls, MOUSE } from 'three-full/builds/Three.es.js';

/**
 * Class to handle the mouse events over the floorplan
 */
export class FloorplanCameraLib {
  /**
   * Set up the controls for the scene
   */
  public static setUpControls(component: FloorplanEditorComponent) {
    component.controls = new OrbitControls(component.camera, component.container);

    component.controlsListener = () => {
      FloorplanCameraLib.updateCameraRotation(component);
      component.camera.updateProjectionMatrix();
      component.forceRender();
      component.changedCamera.emit(component.camera);
    };

    component.controls.addEventListener('change', component.controlsListener);
    FloorplanCameraLib.enableCameraControls(component.controls);
  }

  /**
   * Allows the user to move the camera
   */
  public static enableCameraControls(controls: OrbitControls) {
    controls.enableZoom = true;
    controls.enablePan = true;
    controls.enableRotate = false;
    controls.zoomSpeed = 8;

    controls.mouseButtons = {
      PAN: MOUSE.RIGHT, // Mouse right to move the camera
      ZOOM: MOUSE.MIDDLE, // Wheel to zoom
      // ORBIT: MOUSE.LEFT, (No rotate)
    };
  }

  /**
   * Makes the camera blocked for user interaction
   */
  public static disableCameraControls(controls: OrbitControls) {
    controls.enableZoom = false;
    controls.enablePan = false;
    controls.enableRotate = false;
    controls.mouseButtons = {};
  }

  /**
   * Centers the camera to have the floorplan in the middle adn renders again
   */
  public static centerCamera(component: FloorplanEditorComponent) {
    const props = FloorplanEditorLib.containerProps(component);

    component.camera.left = props.left;
    component.camera.right = props.right;

    component.camera.top = props.top;
    component.camera.bottom = props.bottom;

    component.camera.position.set(0, 0, 90);

    if (component.initialZoom) {
      component.camera.zoom = component.initialZoom;
    }

    component.camera.updateProjectionMatrix();
  }

  /**
   * Initial set up of the scene camera
   * The camera is ready
   */
  public static setUpCamera(component: FloorplanEditorComponent) {
    const props = FloorplanEditorLib.containerProps(component);

    component.camera = new OrthographicCamera(props.left, props.right, props.top, props.bottom, 10, 100);

    // TOP
    component.camera.position.set(0, 0, 90);
    component.camera.rotation.order = 'ZYX';

    component.cameraInfo = {
      rotationX: 0,
      rotationY: 0,
      rotationZ: 0,
    };

    FloorplanCameraLib.updateCameraRotation(component);
    FloorplanCameraLib.setUpControls(component);

    if (component.cameraToKeep) {
      if (component.cameraToKeep.position) {
        component.camera.position.x = component.cameraToKeep.position.x;
        component.camera.position.y = component.cameraToKeep.position.y;
      }
      component.camera.zoom = component.cameraToKeep.zoom;
      component.camera.updateProjectionMatrix();
    }

    component.initialZoom = component.camera.zoom;
  }

  public static updateCameraRotation(component: FloorplanEditorComponent) {
    const cameraRotation = component.camera.rotation;
    if (component.cameraInfo) {
      cameraRotation.x = component.cameraInfo.rotationX;
      cameraRotation.y = component.cameraInfo.rotationY;
      cameraRotation.z = component.cameraInfo.rotationZ;
    }
  }
}
