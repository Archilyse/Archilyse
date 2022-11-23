import { MapView, MapViewEventNames } from '@here/harp-mapview';
import { GeoCoordinates } from '@here/harp-geoutils';
import C from '../../../constants';
import { MapControlsType, SIMULATION_MODE } from '../../../types';
import { UnitControls } from './UnitControls';
import { CameraControls } from './CameraControls';

const testOptions: any = {};
const isProd = window.location.protocol === 'https:';
if (!isProd) {
  // Related: https://stackoverflow.com/a/26790802
  testOptions.preserveDrawingBuffer = true;
}

function setBackground(camera, simType) {
  if (simType === SIMULATION_MODE.THREE_D_VECTOR) {
    return;
  }

  camera.setProperBackground();
}

const DEFAULT_EXTRUDING_BUILDINGS_SETTINGS = {
  // From the default theme (C.HARPGL_THEME)
  id: 'extrudedBuildings',
  description: 'extruded buildings',
  technique: 'extruded-polygon',
  when: ['ref', 'extrudedBuildingsCondition'],
  minZoomLevel: 16,
  renderOrder: 2000,
  height: ['get', 'height'],
  color: ['ref', 'defaultBuildingColor'],
  roughness: 1,
  metalness: 0.8,
  emissive: '#78858C',
  emissiveIntensity: 0.85,
  footprint: true,
  maxSlope: 0.8799999999999999,
  lineWidth: 1,
  lineColor: '#172023',
  lineColorMix: 0.6,
  fadeNear: 0.9,
  fadeFar: 1,
  lineFadeNear: -0.75,
  lineFadeFar: 1,
};
/**
 * Set's up a map centered in Zurich by default
 * @param mapRef
 * @param canvasRef
 * @param greyBg
 */
export function loadMap(mapRef, canvasRef, simType: SIMULATION_MODE): MapControlsType {
  const theme = {
    extends: C.HARPGL_THEME,
    lights: [
      {
        type: 'ambient',
        color: '#ffffff',
        name: 'ambientLight',
        intensity: 0.9,
      },
      {
        type: 'directional',
        color: '#ffffff',
        name: 'light1',
        intensity: 0.7,
        direction: {
          x: 5,
          y: 1,
          z: -3,
        },
        castShadow: true,
      },
    ],
    definitions: {
      // Opaque buildings
      defaultBuildingColor: { value: '#EDE7E1FF' },
    },
    styles: {
      tilezen: [{ ...DEFAULT_EXTRUDING_BUILDINGS_SETTINGS, minZoomLevel: 15 }],
    },
  };
  const map = (mapRef.current = new MapView({
    theme,
    enableShadows: true,
    canvas: canvasRef.current,
    // More than zoom 20 the tiles are not displayed
    maxZoomLevel: 20,
    ...testOptions,
  }));

  const unit = new UnitControls(map);
  const camera = new CameraControls(map);

  setBackground(camera, simType);
  map.addEventListener(MapViewEventNames.ThemeLoaded, () => {
    setBackground(camera, simType);
  });
  map.addEventListener(MapViewEventNames.MovementFinished, event => {
    if (map?.zoomLevel > 18) {
      map.renderLabels = false;
      map.update();
    } else {
      map.renderLabels = true;
      map.update();
    }
  });

  const extension = map.canvas.getContext('webgl').getExtension('WEBGL_lose_context');
  let intervalId;

  map.addEventListener(MapViewEventNames.ContextLost, () => {
    intervalId = setInterval(() => {
      console.warn('<SimulationViewer />: try to restore context');
      extension.restoreContext();
    }, 200);
  });

  map.addEventListener(MapViewEventNames.ContextRestored, () => {
    console.warn('<SimulationViewer />: context has restored');
    clearInterval(intervalId);
  });

  const latitudeZurich = 47.372;
  const longitudeZurich = 8.545;

  // We always start in Zurich as a default
  const startLocation = new GeoCoordinates(latitudeZurich, longitudeZurich);
  map.lookAt({ target: startLocation, zoomLevel: 14.5 });
  map.update();

  return { map, unit, camera };
}
