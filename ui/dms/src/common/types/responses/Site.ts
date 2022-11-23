import Site from '../models/Site';

export type GetSites = {
  ready: boolean;
  lat: string;
  lon: string;
} & Site;
