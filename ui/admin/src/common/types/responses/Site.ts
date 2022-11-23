import SiteModel from '../models/Site';

export type GetSites = {
  ready: boolean;
  lat: string;
  lon: string;
} & SiteModel;
