import { MapControls, MapControlsUI } from '@here/harp-map-controls';
import { MapView, MapViewEventNames } from '@here/harp-mapview';
import C from '../../../constants';
import { SIMULATION_MODE } from '../../../types';
import { DataSource } from '../../SimulationViewer/libs/DataSource';
import { HeatmapHarpMapControls } from '../hooks/useHarpMap';
import HeatmapCameraControls from './HeatmatCameraControls';

const mapViewOptions = {
  theme: C.HARPGL_THEME,
  // Related: https://stackoverflow.com/a/26790802
  preserveDrawingBuffer: process.env.NODE_ENV === 'production',
};

class HarpMapViewRenderer {
  static initMapView = (
    canvas: HTMLCanvasElement,
    options: { dataSource: SIMULATION_MODE; backgroundColor: number }
  ): [MapView, HeatmapCameraControls] => {
    const map = new MapView({ canvas, ...mapViewOptions });
    const camera = new HeatmapCameraControls(map);

    map.addEventListener(MapViewEventNames.ThemeLoaded, () => {
      if (options.dataSource) {
        DataSource.setUpDataSource(map, options.dataSource);
      } else {
        map.renderer.setClearColor(options.backgroundColor || C.HEATMAP_3D_BACKGROUND);
      }
    });

    return [map, camera];
  };

  static setUpEvents = (
    canvas: HTMLCanvasElement,
    mapControls: HeatmapHarpMapControls,
    showMap: boolean
  ): (() => void) => {
    const hanldeWindowResize = () => mapControls.camera.onWindowResize();

    const handleWheel = event => mapControls.camera.onWheel(event);
    const handleKeyDown = event => mapControls.camera.onKeyDown(event);
    const handleMouseDown = event => mapControls.camera.onMouseDown(event);
    const handleMouseUp = () => mapControls.camera.onMouseUp();
    const handleMouseMove = event => mapControls.camera.onMouseMove(event);
    const handleMouseOut = () => mapControls.camera.onMouseOut();

    window.addEventListener('resize', hanldeWindowResize);

    if (showMap) {
      const controls = new MapControls(mapControls.map);
      const uiControls = new MapControlsUI(controls, { zoomLevel: 'input' });
      canvas.parentElement.appendChild(uiControls.domElement);
    } else {
      canvas.addEventListener('wheel', handleWheel);
      canvas.addEventListener('keydown', handleKeyDown);
      canvas.addEventListener('mousedown', handleMouseDown);
      canvas.addEventListener('mouseup', handleMouseUp);
      canvas.addEventListener('mousemove', handleMouseMove);
      canvas.addEventListener('mouseout', handleMouseOut);
    }

    return () => {
      window.removeEventListener('resize', hanldeWindowResize);

      if (!showMap) {
        canvas.removeEventListener('wheel', handleWheel);
        canvas.removeEventListener('keydown', handleKeyDown);
        canvas.removeEventListener('mousedown', handleMouseDown);
        canvas.removeEventListener('mouseup', handleMouseUp);
        canvas.removeEventListener('mousemove', handleMouseMove);
        canvas.removeEventListener('mouseout', handleMouseOut);
      }
    };
  };
}

export default HarpMapViewRenderer;
