import {
  PAGE_SIZES,
  SCALING_BASELINE,
  SCALING_MAX_DIFF_BETWEEN_MEASUREMENTS,
  SeparatorsType,
} from '../../../constants';
import ScaleMeasurement from '../../../types/ScaleMeasurement';
import {
  convertPixelsToCMs,
  getAreaSizeInPixels,
  getLineDistance,
  isLine,
  isPolygon,
  orderVertices,
} from '../../../utils/geometry';
import { getSelectedLayer } from '../../../utils/state-utils';

const isMeasurementOutlier = (measurements: ScaleMeasurement[], currentMeasurement) => {
  if (!measurements || !currentMeasurement) return false;

  const currentScaleFactor = calculateScale(currentMeasurement);
  const currentMeasurementDistanceInCm = convertPixelsToCMs(currentScaleFactor, SCALING_BASELINE);
  const differsTooMuchFromOtherMeasurements = measurements.some(m => {
    const scaleFactor = calculateScale(m);
    const distInCM = convertPixelsToCMs(scaleFactor, SCALING_BASELINE);
    return Math.abs(distInCM - currentMeasurementDistanceInCm) > SCALING_MAX_DIFF_BETWEEN_MEASUREMENTS;
  });
  return differsTooMuchFromOtherMeasurements;
};

const needsRepeating = measurements => {
  const [lastMeasurement] = measurements.slice(-1);
  return isMeasurementOutlier(measurements, lastMeasurement);
};

// The scale calculated is always the area scale factor, hence the Math.pow in the line section
const calculateScale = ({ points, distance, areaSize, area }: ScaleMeasurement): number => {
  if (isLine(points)) {
    const currentDistance = getLineDistance(points);
    return !isNaN(currentDistance) && currentDistance ? Math.pow(distance / currentDistance, 2) : 0;
  } else if (isPolygon(points) && area) {
    const currentAreaSize = getAreaSizeInPixels(area) / 10000;
    const result = !isNaN(currentAreaSize) && currentAreaSize ? areaSize / currentAreaSize : 0;
    return result;
  }
};

const getAverageScaleFactor = (measurements: ScaleMeasurement[]): number => {
  const scaleFactorMeasurements = measurements.reduce((prevScale, nextMeasurement) => {
    const nextScaleMeasurement = calculateScale(nextMeasurement);
    return prevScale + nextScaleMeasurement;
  }, 0);
  return scaleFactorMeasurements / measurements.length;
};

const calculateScaleFactorFromPageSpecs = (scaleRatio, paperFormat, sceneBackground) => {
  const currentPageSizes = PAGE_SIZES[paperFormat];
  const widthPxPerCm = sceneBackground.width / currentPageSizes.width;
  const heightPxPerCm = sceneBackground.height / currentPageSizes.height;

  // pixels per centimeters
  const pageFormat = (widthPxPerCm + heightPxPerCm) / 2;

  const scaleCm = scaleRatio / pageFormat;
  const scaleFactor = scaleCm ** 2;

  return scaleFactor;
};

const getPointsFromScaleToolLines = state => {
  const selectedLayer = getSelectedLayer(state.scene);
  const lines = Object.values(selectedLayer.lines);
  const points = lines
    .filter((line: any) => line.type === SeparatorsType.SCALE_TOOL)
    .reduce((accum: any[], line: any) => {
      const vertices = line.vertices.map(vertexID => {
        const vertex = selectedLayer.vertices[vertexID];
        return { x: vertex.x, y: vertex.y };
      });

      const orderedVertices = orderVertices(vertices);
      return [...accum, ...orderedVertices];
    }, []);
  return points;
};

export {
  isMeasurementOutlier,
  calculateScale,
  calculateScaleFactorFromPageSpecs,
  getAverageScaleFactor,
  needsRepeating,
  getPointsFromScaleToolLines,
};
