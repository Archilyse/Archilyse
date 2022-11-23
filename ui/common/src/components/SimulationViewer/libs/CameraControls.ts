import { MapView, MapViewUtils } from '@here/harp-mapview';
import { GeoCoordinates } from '@here/harp-geoutils';
import C from '../../../constants';
import { LatLngAltTuple } from '../../../types';

const { DASHBOARD_3D_BACKGROUND, HEATMAP_3D_BACKGROUND, DEFAULT_3D_BACKGROUND } = C;

const MIN_INCLINATION = 0;
const MAX_INCLINATION = 90;

export class CameraControls {
  rotationFromNorth;
  distance;
  min_distance;
  max_distance;

  rotateDirection = 0;
  inclinationDirection = 0;

  rotateInterval = null;
  inclinationInterval = null;
  camPosition: LatLngAltTuple = null;

  // The camera looking to the rendered units (45 degrees)
  inclinationDegrees = 65;

  map;

  constructor(map: MapView) {
    this.reset();
    this.map = map;
  }

  reset() {
    this.rotationFromNorth = 0;
    this.distance = 150;
    this.min_distance = 50;
    this.max_distance = 500;
  }

  setPosition(camPosition) {
    this.camPosition = camPosition;
  }

  setDistance(distance) {
    this.distance = distance;
  }

  changeDistance(incDistance) {
    this.distance += incDistance;
  }

  handleKeyDown(event) {
    try {
      const KEY_LEFT = 37;
      const KEY_RIGHT = 39;
      const KEY_UP = 38;
      const KEY_DOWN = 40;

      const ROTATE_SPEED = 8; // Degrees per interval
      const INCLINATION_SPEED = 4;

      if (event.keyCode === KEY_LEFT) {
        this.rotateDirection = -ROTATE_SPEED;
        this.setUpRotation();
      }
      if (event.keyCode === KEY_RIGHT) {
        this.rotateDirection = ROTATE_SPEED;
        this.setUpRotation();
      }

      if (event.keyCode === KEY_UP) {
        this.inclinationDirection = -INCLINATION_SPEED;
        this.setUpInclination();
      }
      if (event.keyCode === KEY_DOWN) {
        this.inclinationDirection = INCLINATION_SPEED;
        this.setUpInclination();
      }
    } catch (e) {
      console.error(e);
    }
  }

  handleKeyUp() {
    try {
      this.stopRotation();
      this.stopInclination();
    } catch (e) {
      console.error(e);
    }
  }

  /**
   * Sets an interval to inclinatate the building in "this.inclinationDirection"
   */
  setUpInclination() {
    if (this.inclinationInterval === null) {
      // Every 0.1 secs we increase the angle giving a smooth rotation
      const INC_INTERVAL_TIME = 100;

      this.inclinationInterval = setInterval(() => {
        const newInclination = this.inclinationDegrees + this.inclinationDirection;
        if (newInclination < MIN_INCLINATION || newInclination > MAX_INCLINATION) {
          return;
        }

        this.inclinationDegrees += this.inclinationDirection;
        this.cameraSetUp();
      }, INC_INTERVAL_TIME);
    }
  }

  /**
   * Sets an interval to rotate the building in "this.rotateDirection"
   */
  setUpRotation() {
    if (this.rotateInterval === null) {
      // Every 0.1 secs we increase the angle giving a smooth rotation
      const ROTATION_INTERVAL_TIME = 100;

      this.rotateInterval = setInterval(() => {
        this.rotationFromNorth += this.rotateDirection;
        this.cameraSetUp();
      }, ROTATION_INTERVAL_TIME);
    }
  }

  /**
   * Stop the interval and back to neutral rotation
   */
  stopRotation() {
    if (this.rotateInterval) {
      clearInterval(this.rotateInterval);
      this.rotateInterval = null;
    }
    this.rotateDirection = 0;
  }

  /**
   * Stop the interval and back to neutral inclination
   */
  stopInclination() {
    if (this.inclinationInterval) {
      clearInterval(this.inclinationInterval);
      this.inclinationInterval = null;
    }
    this.inclinationDirection = 0;
  }

  /**
   * Camera calculations given coordinates to look at, angle and distance
   */
  cameraSetUp() {
    this.map.camera.near = Number.MIN_SAFE_INTEGER;
    this.map.camera.updateProjectionMatrix();

    const targetCoordinates = new GeoCoordinates(...this.camPosition);
    const initialZoomLevel = 19.9;

    const targetPosition = MapViewUtils.getCameraPositionFromTargetCoordinates(
      targetCoordinates,
      this.distance,
      this.rotationFromNorth,
      this.inclinationDegrees,
      this.map.projection
    );

    const targetQuaternion = MapViewUtils.getCameraRotationAtTarget(
      this.map.projection,
      targetCoordinates,
      this.rotationFromNorth,
      this.inclinationDegrees
    );

    this.map.setCameraGeolocationAndZoom(
      targetCoordinates,
      initialZoomLevel,
      this.rotationFromNorth,
      this.inclinationDegrees
    );

    this.map.camera.position.copy(targetPosition);
    this.map.camera.quaternion.copy(targetQuaternion);
    this.map.camera.updateMatrixWorld(true);

    this.map.update();
  }

  setMapBackground(color) {
    this.map.renderer.setClearColor(color, 1);
    if (this.map.theme?.['sky']) {
      this.map.theme['sky']['bottomColor'] = color;
      this.map.theme['sky']['groundColor'] = color;
      this.map.theme['sky']['topColor'] = color;
    }
    this.map.update();
  }

  setGreyBackground() {
    this.setMapBackground(HEATMAP_3D_BACKGROUND);
  }

  setProperBackground() {
    this.setMapBackground(DASHBOARD_3D_BACKGROUND);
  }

  setDefaultBackground() {
    this.setMapBackground(DEFAULT_3D_BACKGROUND);
  }
}
