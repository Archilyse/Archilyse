import { useEffect, useState } from 'react';
import { MapControls, MapControlsUI } from '@here/harp-map-controls';
import { MapViewEventNames } from '@here/harp-mapview';
import { MapControlsType, SIMULATION_MODE } from '../../../types';
import C from '../../../constants';
import { DataSource } from '../libs/DataSource';
import { loadMap } from '../libs/MapControls';
import { removePreviousBuildings } from '../libs/UnitRenderer';
import backup3dMapTheme from '../../../../assets/backup3dMapTheme.json'; // Same as https://unpkg.com/@here/harp-map-theme@0.28.0/resources/berlin_tilezen_base.json, but without external assets

const { MAP_TILES_TO_DISPLAY } = C;
const { EVENT_KEYDOWN, EVENT_KEYUP, EVENT_RESIZE } = C;

const intialMapControls: MapControlsType = {
  map: null,
  unit: null,
  camera: null,
};

const isMapThemeLoadedSuccessfully = map => map.m_themeManager.m_theme.lights?.length > 0;

const setUpEvents = (canvasRef, mapControls) => {
  const onWindowResize = () => {
    try {
      const { offsetWidth, offsetHeight } = canvasRef.current;
      mapControls.map.resize(offsetWidth, offsetHeight);
      mapControls.map.update();
    } catch (e) {
      console.log('Error while resizing canvas');
    }
  };
  const handleKeyDown = event => mapControls.camera.handleKeyDown(event);
  const handleKeyUp = () => mapControls.camera.handleKeyUp();

  window.addEventListener(EVENT_RESIZE, onWindowResize);
  canvasRef.current.addEventListener(EVENT_KEYDOWN, handleKeyDown);
  canvasRef.current.addEventListener(EVENT_KEYUP, handleKeyUp);

  // Unsubscribe when unmount
  return function cleanup() {
    try {
      window.removeEventListener(EVENT_RESIZE, onWindowResize);
      canvasRef.current.removeEventListener(EVENT_KEYDOWN, handleKeyDown);
      canvasRef.current.removeEventListener(EVENT_KEYUP, handleKeyUp);

      if (mapControls.map) {
        removePreviousBuildings(mapControls.map);
        mapControls.map.dispose();
      }

      // We don't want the app to crash if removing the listeners fail
    } catch (e) {
      console.log('Error unsubscribing from simulation viewer', e);
    }
  };
};

const addControlsToMap = (canvasRef, mapRef) => {
  if (canvasRef.current && mapRef.current) {
    const controls = new MapControls(mapRef.current);
    const uiControls = new MapControlsUI(controls, { zoomLevel: 'input' });
    canvasRef.current.parentElement.appendChild(uiControls.domElement);
  }
};

const removeControlsFromMap = canvasRef => {
  if (canvasRef.current && canvasRef.current.parentElement) {
    const canvas = canvasRef.current.parentElement;
    canvasRef.current.parentElement.childNodes.forEach(child => {
      if (child.classList?.contains('harp-gl_controls')) {
        canvas.removeChild(child);
      }
    });
  }
};

const setUpControls = ({ canvasRef, mapRef, simType }) => {
  if (simType === SIMULATION_MODE.DASHBOARD) {
    removeControlsFromMap(canvasRef);
  } else {
    addControlsToMap(canvasRef, mapRef);
  }
};

const setUpCamera = (mapControls, simType) => {
  if (!mapControls || !mapControls.map) return;

  DataSource.setUpDataSource(mapControls.map, simType);

  if (simType === SIMULATION_MODE.THREE_D_VECTOR) {
    mapControls.camera.setDefaultBackground();
  } else if (simType === SIMULATION_MODE.DASHBOARD) {
    mapControls.camera.setProperBackground();
  }
};

let attemptedToLoadBackupTheme = false;

const use3dMap = ({ canvasRef, mapRef, simType }): any => {
  const [mapControls, setMapControls] = useState<MapControlsType>(intialMapControls);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(null);

  const loadBackupTheme = async (mapCtrl: MapControlsType) => {
    console.warn('Loading default 3d map theme...');
    if (attemptedToLoadBackupTheme) {
      // Otherwise there could be an infinite loop
      console.error(`Error loading backup 3d theme, this should not happen`);
      setError('Error loading map, contact support');
      return;
    }
    attemptedToLoadBackupTheme = true;
    // @ts-ignore
    await mapCtrl.map.setTheme(backup3dMapTheme);
    setLoaded(true);
  };

  const loadInitialData = async (mapCtrl, simType) => {
    mapCtrl.map.addEventListener(MapViewEventNames.ThemeLoaded, async event => {
      DataSource.setUpDataSource(mapCtrl.map, simType);
      mapCtrl.map.visibleTileSet.setNumberOfVisibleTiles(MAP_TILES_TO_DISPLAY);

      if (isMapThemeLoadedSuccessfully(event.target)) {
        setLoaded(true);
      } else {
        await loadBackupTheme(mapCtrl);
      }
    });
  };

  useEffect(() => {
    const mapCtrl = loadMap(mapRef, canvasRef, simType);
    setMapControls(mapCtrl);
    loadInitialData(mapCtrl, simType);
    return setUpEvents(canvasRef, mapCtrl);
  }, []);

  useEffect(() => {
    if (!mapControls.map) return;
    setUpControls({ canvasRef, simType, mapRef });
    setUpCamera(mapControls, simType);
  }, [mapControls, simType]);

  if (loaded) {
    return { loaded, mapControls, error };
  } else {
    return { loaded, mapControls: {}, error }; // As a lot of logic equals `mapControls.map` === loaded map, to explicitly indicate map is not loaded
  }
};

export default use3dMap;
