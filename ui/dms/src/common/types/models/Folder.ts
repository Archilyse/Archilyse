type Folder = {
  id: number;
  name: string;
  labels: string[];
  created: string;
  isEntity?: boolean; // Means this is a folder created in the folder collection to represent an entity (e.g. rooms)
  type: 'custom_folder';
  updated: string;
};

export default Folder;
