import { Polygon } from '@turf/turf';
import { FeatureCollection } from 'geojson';

type RetrievePredictionResponse = FeatureCollection<Polygon>;

export default RetrievePredictionResponse;
