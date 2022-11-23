import create from 'zustand';
import { ProviderLocalStorage } from 'Providers';
import { DataViewType, DMSState } from 'Common/types';
import { C } from 'Common';

const { VIEWS } = C;

const getInitialView = (): DataViewType => {
  const savedView = ProviderLocalStorage.get(C.STORAGE.VIEW) as DataViewType;
  if (savedView) return savedView;
  return VIEWS.TABLE;
};

const shallowClone = arrayOfObj => (arrayOfObj || []).map(a => ({ ...a }));

// @TODO: Generate an immutable state using immer or something similar
// @TODO: Rename customFolders & entityFiles to folders & files in the future
const useStore = create<DMSState>(set => ({
  customFolders: [],
  entityFiles: [],
  filter: '',
  hoveredItem: null,
  itemInClipboard: null,
  openedFile: null,
  originalClipboardLocation: '',
  entities: [],
  mapSites: [],
  currentUnits: [],
  snackbarStatus: { open: false, message: '', severity: '' },
  view: getInitialView(),
  visibleItems: [],
  setCustomFolders: customFolders => set({ customFolders: shallowClone(customFolders) }),
  setEntityFiles: entityFiles => set({ entityFiles: shallowClone(entityFiles) }),
  setFilter: filter => set({ filter }), // @TODO: Reset it on path change
  setHoveredItem: hoveredItem => set({ hoveredItem }),
  setItemInClipboard: itemInClipboard => set({ itemInClipboard }),
  setOriginalClipboardLocation: originalClipboardLocation => set({ originalClipboardLocation }),
  setVisibleItems: visibleItems => set({ visibleItems: shallowClone(visibleItems) }),
  setEntities: entities => set({ entities: shallowClone(entities) }),
  setMapSites: mapSites => set({ mapSites: shallowClone(mapSites) }),
  setOpenedFile: openedFile => set({ openedFile }),
  setCurrentUnits: currentUnits => set({ currentUnits: shallowClone(currentUnits) }),
  setView: view => set({ view }),
}));

export default useStore;
