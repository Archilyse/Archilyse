type Pipeline = {
  building_housenumber: string;
  building_id: number;
  classified: boolean;
  client_building_id: string;
  client_site_id: null;
  created: Date;
  floor_numbers: number[];
  georeferenced: boolean;
  id: number;
  is_masterplan: false;
  labelled: boolean;
  splitted: boolean;
  units_linked: boolean;
  updated: Date;
};

export default Pipeline;
