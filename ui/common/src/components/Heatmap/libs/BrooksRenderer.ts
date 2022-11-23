import { LatLngTuple } from 'leaflet';
import { BrooksType } from '../../../types';
import { drawAnnotations } from '../../SimulationViewer/libs/AnnotationsRenderer';
import { HeatmapHarpMapControls } from '../hooks/useHarpMap';

class BrooksRenderer {
  /**
   * To find coordinates of center we collect lat/lng coordinates of separators (walls, ralings...)
   * and calculate center of both
   */
  static findCenterCoords = (brooks: BrooksType): LatLngTuple => {
    const [lats, lngs] = BrooksRenderer._getSeparatorsCoords(brooks);

    const centerLat = (Math.max(...lats) + Math.min(...lats)) / 2;
    const centerLng = (Math.max(...lngs) + Math.min(...lngs)) / 2;

    return [centerLat, centerLng];
  };

  static findEdgeCoords = (brooks: BrooksType): [LatLngTuple, LatLngTuple] => {
    const [lats, lngs] = BrooksRenderer._getSeparatorsCoords(brooks);

    return [
      [Math.min(...lats), Math.min(...lngs)],
      [Math.max(...lats), Math.max(...lngs)],
    ];
  };

  static drawBrooks = (brooks: BrooksType, mapControls: HeatmapHarpMapControls, withFeatures = false): void => {
    const { map, camera } = mapControls;

    const center: LatLngTuple = BrooksRenderer.findCenterCoords(brooks); // @TODO: Proably this could be erased, review

    if (!camera.position) {
      const edgeCoords = BrooksRenderer.findEdgeCoords(brooks);
      camera.setLimits(edgeCoords);
      camera.setDistance(edgeCoords);

      camera.lookOverCoordinate(center);
    }

    drawAnnotations(map, brooks.separators, { drawEdges: false });
    drawAnnotations(map, brooks.openings, { drawEdges: false });

    if (withFeatures) {
      drawAnnotations(map, brooks.features, { drawEdges: true });
    }

    map.update();
  };

  static _getSeparatorsCoords = (brooks: BrooksType): [number[], number[]] => {
    const lats = [];
    const lngs = [];

    for (const polygons of Object.values(brooks.separators)) {
      polygons.forEach(polygon => {
        lats.push(polygon.geometry.coordinates[0][0][0]);
        lngs.push(polygon.geometry.coordinates[0][0][1]);
      });
    }

    return [lats, lngs];
  };
}

export default BrooksRenderer;
