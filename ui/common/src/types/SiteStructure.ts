import Building from './Building';
import Floor from './Floor';

export type BuildingWithFloors = Building & { floors: { [id: string]: Floor } };

type SiteStructure = {
  id: number;
  buildings: BuildingWithFloors[];
  client_site_id?: string;
  name: string;
  enforce_masterplan?: boolean;
};

export default SiteStructure;
