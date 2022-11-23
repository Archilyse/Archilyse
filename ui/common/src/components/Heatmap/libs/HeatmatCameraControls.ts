import { MapView, MapViewUtils } from '@here/harp-mapview';
import { GeoCoordinates } from '@here/harp-geoutils';
import { LatLngTuple } from 'leaflet';

type CameraPosition = [number, number, number];

const DEFAULT_CAMERA_DISTANCE = 300;
const MIN_CAMERA_DISTANCE = 5;
const MAX_CAMERA_DISTANCE = 350;

class HeatmapCameraControls {
  map: MapView;
  mapSource;

  position: CameraPosition = null;
  positionLimits = { min: null, max: null };
  distance = { current: DEFAULT_CAMERA_DISTANCE, min: MIN_CAMERA_DISTANCE, max: MAX_CAMERA_DISTANCE };
  rotationFromNorth = 0;
  inclinationDegrees = 0;

  mouseMeta = { clicked: false, x: 0, y: 0 };

  constructor(harpMap: MapView) {
    this.map = harpMap;
  }

  lookOverCoordinate(coordinate: LatLngTuple): void {
    const [lat, lng] = coordinate;
    this.position = [lat, lng, 0];

    this._updateCamera();
  }

  /**
   * To set distance over given coordinates we calculate latitude and longituted lines
   * based on max and min values and find perimeter of recieved rectangle
   */
  setDistance(coordinates: [LatLngTuple, LatLngTuple]): void {
    const [latMin, lngMin] = coordinates[0];
    const [latMax, lngMax] = coordinates[1];

    const latDistance = latMax - latMin;
    const lngDistance = lngMax - lngMin;

    const { clientHeight, clientWidth } = this.map.canvas;

    const DELTA = 200; // was found by selection method
    const ratio = clientHeight > clientWidth ? clientHeight / clientWidth : clientHeight / clientHeight;
    const perimeter = (latDistance + lngDistance) * 2;

    this.distance.current = DEFAULT_CAMERA_DISTANCE * perimeter * ratio * DELTA;
  }

  setLimits(coordinates: [LatLngTuple, LatLngTuple]): void {
    const DELTA = 0.00005; // was found by selection method
    const [latMin, lngMin] = coordinates[0];
    const [latMax, lngMax] = coordinates[1];

    this.positionLimits = { min: [latMin - DELTA, lngMin - DELTA], max: [latMax + DELTA, lngMax + DELTA] };
  }

  onWindowResize(): void {
    try {
      const { offsetWidth, offsetHeight } = this.map.canvas;
      this.map.resize(offsetWidth, offsetHeight);

      this.map.update();
    } catch (error) {
      console.log('Error while resizing canvas', error);
    }
  }

  onWheel(event: WheelEvent): void {
    event.preventDefault();
    event.stopPropagation();

    const isFirefox = event.deltaMode === 1;
    const DELTA_DISTANCE = isFirefox ? 1 : 20;
    const deltaY = event.deltaY;

    let newDistance = this.distance.current + deltaY / DELTA_DISTANCE;
    if (newDistance > this.distance.max) newDistance = this.distance.max;
    if (newDistance < this.distance.min) newDistance = this.distance.min;

    this.distance.current = newDistance;
    this._updateCamera();
  }

  onKeyDown(event: KeyboardEvent): void {
    const DELTA = 5e-5; // was found by selection method

    if (event.key === 'ArrowUp') {
      const newPosition = this.position[0] + DELTA;
      if (newPosition < this.positionLimits.max[0]) this.position[0] = newPosition;
    }
    if (event.key === 'ArrowDown') {
      const newPosition = this.position[0] - DELTA;
      if (newPosition > this.positionLimits.min[0]) this.position[0] = newPosition;
    }
    if (event.key === 'ArrowRight') {
      const newPosition = this.position[1] + DELTA;
      if (newPosition < this.positionLimits.max[1]) this.position[1] = newPosition;
    }
    if (event.key === 'ArrowLeft') {
      const newPosition = this.position[1] - DELTA;
      if (newPosition > this.positionLimits.min[1]) this.position[1] = newPosition;
    }

    this._updateCamera();
  }

  onMouseDown(event: MouseEvent): void {
    this.mouseMeta = { clicked: true, x: event.clientX, y: event.clientY };
  }

  onMouseUp(): void {
    this.mouseMeta = { clicked: false, x: 0, y: 0 };
  }

  onMouseOut(): void {
    this.mouseMeta = { clicked: false, x: 0, y: 0 };
  }

  onMouseMove(event: MouseEvent): void {
    if (!this.mouseMeta.clicked) return;

    event.preventDefault();
    event.stopPropagation();

    const DELTA = 5e-7; // was found by selection method
    const currentX = event.clientX;
    const currentY = event.clientY;

    const dx = (this.mouseMeta.x - currentX) * DELTA;
    const dy = (this.mouseMeta.y - currentY) * DELTA * -1; // (-1) to invert mouse

    this.mouseMeta = { ...this.mouseMeta, x: currentX, y: currentY };

    const newPosition: CameraPosition = [this.position[0] + dy, this.position[1] + dx, 0];
    if (this._isInsideLimits(newPosition)) {
      this.position = newPosition;
      this._updateCamera();
    }
  }

  _updateCamera(): void {
    if (!this.position) return; // https://sentry.io/organizations/archilyse/issues/2273645684/?project=1731932&referrer=jira_integration

    this.map.camera.near = Number.MIN_SAFE_INTEGER;
    this.map.camera.updateProjectionMatrix();

    const targetCoordinates = new GeoCoordinates(...this.position);

    const targetPosition = MapViewUtils.getCameraPositionFromTargetCoordinates(
      targetCoordinates,
      this.distance.current,
      this.rotationFromNorth,
      this.inclinationDegrees,
      this.map.projection
    );

    this.map.camera.position.copy(targetPosition);
    this.map.camera.updateMatrixWorld(true);

    this.map.update();
  }

  _isInsideLimits(newPosition: CameraPosition): boolean {
    const [lat, lng, _] = newPosition;
    const isLatInsideLimit = lat < this.positionLimits.max[0] && lat > this.positionLimits.min[0];
    const isLngInsideLimit = lng < this.positionLimits.max[1] && lng > this.positionLimits.min[1];

    return isLatInsideLimit && isLngInsideLimit;
  }
}

export default HeatmapCameraControls;
