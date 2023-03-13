import { LatLngTuple } from 'leaflet';
import { LatLngAltTuple } from '../../../types';
import { drawHexagons } from '../../SimulationViewer/libs/SimRenderer';
import { HeatmapHarpMapControls } from '../hooks/useHarpMap';

const hexPadding = 0.05;
class HeatmapRenderer {
  static getRadiusByResolution = (resolution: number): number => {
    return resolution - hexPadding; // Keeping padding
  };

  /**
   * To find coordinates of center we go naive and collect lat/lng coordinates then calculate center of both
   */
  static findCenterCoordinate = (observationPoints: LatLngAltTuple[]): LatLngTuple => {
    const [lats, lngs] = HeatmapRenderer._getCoordinates(observationPoints);

    const latCenter = (Math.max(...lats) + Math.min(...lats)) / 2;
    const lngCenter = (Math.max(...lngs) + Math.min(...lngs)) / 2;

    return [latCenter, lngCenter];
  };

  static findEdgeCoords = (observationPoints: LatLngAltTuple[]): [LatLngTuple, LatLngTuple] => {
    const [lats, lngs] = HeatmapRenderer._getCoordinates(observationPoints);

    return [
      [Math.min(...lats), Math.min(...lngs)],
      [Math.max(...lats), Math.max(...lngs)],
    ];
  };

  static drawHeatmap = (
    heatmap: number[],
    localObservationPoints: LatLngAltTuple[],
    totalObservationPoints: LatLngAltTuple[],
    mapControls: HeatmapHarpMapControls,
    valueToColor: (value) => string,
    options = {
      rotationToNorth: 0,
      hexagonRadius: 0.2,
      showMap: false,
    }
  ): void => {
    const { map, camera } = mapControls;

    let cameraGeoCoordinates;
    if (!camera.position) {
      const edgeCoords = HeatmapRenderer.findEdgeCoords(totalObservationPoints);
      camera.setLimits(edgeCoords);

      if (!options.showMap) camera.setDistance(edgeCoords);
      const center = HeatmapRenderer.findCenterCoordinate(totalObservationPoints);
      camera.lookOverCoordinate(center);

      cameraGeoCoordinates = camera.position;
    } else {
      const geoPosition = map.projection.unprojectPoint(map.camera.position);
      cameraGeoCoordinates = [geoPosition.latitude, geoPosition.longitude, 0];
    }

    drawHexagons(
      map,
      heatmap,
      localObservationPoints,
      valueToColor,
      options.rotationToNorth,
      cameraGeoCoordinates,
      options.hexagonRadius
    );

    map.update();
  };

  static _getCoordinates = (observationPoints: LatLngAltTuple[]): [number[], number[]] => {
    const lats = observationPoints.map(point => point[0]);
    const lngs = observationPoints.map(point => point[1]);
    return [lats, lngs];
  };
}

export default HeatmapRenderer;
