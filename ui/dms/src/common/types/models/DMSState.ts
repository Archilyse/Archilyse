import { GetSites } from '../responses/Site';
import SnackbarStatusType from '../SnackbarStatusType';
import DataViewType from '../DataViewType';
import Folder from './Folder';
import File from './File';
import DMSItem from './DMSItem';
import OpenedFile from './OpenedFile';

type DMSState = {
  customFolders: Folder[];
  entityFiles: File[];
  filter: string;
  hoveredItem: DMSItem;
  itemInClipboard: File | Folder;
  originalClipboardLocation: string;
  openedFile: OpenedFile;
  entities: any[];
  mapSites: GetSites[];
  currentUnits: any[];
  snackbarStatus: SnackbarStatusType;
  view: DataViewType;
  visibleItems: DMSItem[];
  setCustomFolders: (customFolders: Folder[]) => void;
  setEntityFiles: (files: File[]) => void;
  setFilter: (filter: string) => void;
  setHoveredItem: (item: DMSItem) => void;
  setVisibleItems: (item: DMSItem[]) => void;
  setItemInClipboard: (item: File | Folder) => void;
  setOriginalClipboardLocation: (string) => void;
  setOpenedFile: (file: OpenedFile) => void;
  setEntities: (entities: any) => void;
  setMapSites: (sites: GetSites[]) => void;
  setCurrentUnits: (sites: any[]) => void;
  setView: (view: DataViewType) => void;
};

export default DMSState;
