type BasicEntity = {
  id: number;
  name: string;
  clientSiteId?: string;
  created?: string;
  labels?: string[];
  phPrice?: number;
  phFactor?: number;
  type?: 'folder-clients' | 'folder-sites' | 'folder-buildings' | 'folder-floors' | 'folder-units' | 'folder-rooms';
};

export default BasicEntity;
