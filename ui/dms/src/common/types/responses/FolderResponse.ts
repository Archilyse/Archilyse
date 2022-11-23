type FolderResponse = {
  building_id: number;
  client_id: number;
  created: string;
  creator_id: number;
  deleted: boolean;
  floor_id: number;
  id: number;
  labels: string[];
  name: string;
  parent_folder_id: number;
  site_id: number;
  unit_id: number;
  updated: null;
};

export default FolderResponse;
