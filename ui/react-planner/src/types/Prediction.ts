import { Feature, Polygon } from 'geojson';

type Prediction = {
  lines: Feature<Polygon>[];
  holes: Feature<Polygon>[];
  items: Feature<Polygon>[];
};

export default Prediction;
