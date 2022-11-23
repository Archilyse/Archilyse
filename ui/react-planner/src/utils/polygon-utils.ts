import { Line } from '../types';

export const coordsToSVGPoints = (coords: Line['coordinates']) => {
  const [innerPolygonCoordinates] = coords;
  return innerPolygonCoordinates.map(point => point.join(', ')).join(' ');
};
