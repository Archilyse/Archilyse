import React, { useContext, useEffect, useLayoutEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { SnackbarContext } from 'archilyse-ui-components';
import { C } from 'Common';
import { useHierarchy, useRouter } from 'Common/hooks';
import { AreaData, File, Folder, GetSitesResponse, ParentQuery } from 'Common/types';
import { getFile } from 'Common/modules';
import { ProviderRequest } from 'Providers';
import { NewFolderDialog, RenameDialog, SelectedView } from './components';
import { getEntityId, getUserClientId, inView, isEntityFolder, parseOpenedFile } from './modules';
import { useFetchData, useStore } from './hooks';
import './dataView.scss';

const { DMS_VIEWS, CUSTOM_FOLDER_TYPE } = C;
const { SITES, FLOORS, BUILDINGS, TRASH, CUSTOM_FOLDER, UNITS, ROOMS } = DMS_VIEWS;

type Props = {
  data: GetSitesResponse[] | any[]; // @TODO: change any with another types
  isLoadingEntities?: boolean;
  onClickFolder?: (folder: any) => void;
  getEntityName?: (folder: GetSitesResponse | any) => string;
};

type FileHandlersType = {
  allowedUpload: boolean;
  onAddComment: (item: any, comment: any) => void;
  onUploadFile: (event: React.SyntheticEvent) => void;
  onCreateFolder: (event: React.SyntheticEvent) => void;
  onMoveToTrash: (item: File | Folder) => void;
  onChangeTags: (item: File | Folder) => void;
  onDownload: (file: File) => void;
  onDelete: (item: File | Folder) => void;
  onRestore: (item: File | Folder) => void;
  onRename: (item: File | Folder, newName: string, showSnackBar: false) => void;
  onPaste: (item: File | Folder) => void;
};

const ENTITY_KEYS_FROM_SITES = ['site_id', 'building_id', 'floor_id', 'unit_id'];

const parseBackendAreaData = (netAreaData, pathname): AreaData => {
  const currentLevel: string = (pathname || '').split('/')[1];
  if (inView([FLOORS], pathname)) {
    return {
      // Units are needed to compute correct PH prices in `filterAndParseData`
      floors: Object.entries(netAreaData?.floors || {}).map(([id, netArea]: [string, number]) => ({ id, netArea })),
      units: Object.entries(netAreaData?.units || {}).map(([id, netArea]: [string, number]) => ({ id, netArea })),
    };
  }

  return {
    [currentLevel]: Object.entries(netAreaData || {})
      .map(([id, netArea]: [string, number]) => ({ id, netArea }))
      .filter(({ id }) => id), // In rooms we could have areas (i.e public spaces) without the corresponding UI folder here
  };
};

const getFloorPlanIdFromHierarchy = hierarchy => {
  const unitHierarchyEntity = hierarchy[hierarchy.length - 1];

  if (!unitHierarchyEntity?.href?.includes?.('floor_id')) return null;

  return unitHierarchyEntity.payload?.plan_id;
};

const getUnitIdsByView = (entities, pathname, query) => {
  if (inView([UNITS], pathname)) return entities.map(entity => entity.id);
  if (inView([ROOMS], pathname)) return [Number(query.unit_id)];
};

function DataView({
  data,
  isLoadingEntities = false,
  onClickFolder = () => null,
  getEntityName = null,
}: Props): JSX.Element {
  const { pathname, query }: { pathname: string; query: ParentQuery } = useRouter();
  const hierarchy = useHierarchy();
  const history = useHistory();

  const customFolders = useStore(state => state.customFolders);
  const entityFiles = useStore(state => state.entityFiles);
  const filter = useStore(state => state.filter);
  const entities = useStore(state => state.entities);
  const view = useStore(state => state.view);
  const setCustomFolders = useStore(state => state.setCustomFolders);
  const setHoveredItem = useStore(state => state.setHoveredItem);
  const setItemInClipboard = useStore(state => state.setItemInClipboard);
  const setEntities = useStore(state => state.setEntities);
  const setMapSites = useStore(state => state.setMapSites);
  const setCurrentUnits = useStore(state => state.setCurrentUnits);
  const setEntityFiles = useStore(state => state.setEntityFiles);
  const setOpenedFile = useStore(state => state.setOpenedFile);

  const snackbar = useContext(SnackbarContext);
  const showSnackbar = data =>
    snackbar.show({ muiProps: { anchorOrigin: { vertical: 'bottom', horizontal: 'right' } }, ...data });

  const {
    unitFloorPlanBlob,
    netAreaData,
    files,
    folders,
    site,
    siteUnits,
    unit,
    reloadFiles,
    reloadCustomFolders,
    loadingState,
  } = useFetchData(view, hierarchy, isLoadingEntities);

  const [showNewFolderDialog, setShowNewFolderDialog] = useState(false);
  const [showRenameDialog, setShowRenameDialog] = useState({ open: false, label: '', item: null });

  const handleRenameDialogClose = () => setShowRenameDialog(dialog => ({ ...dialog, open: false }));
  const handleRenameDialogOpen = item => {
    let label = 'File name';
    if (showRenameDialog.item == CUSTOM_FOLDER_TYPE) {
      label = 'Folder name';
    }
    setShowRenameDialog({ open: true, label, item });
  };

  // Layout effect is needed so `isEmptyData`receives in sync info in <SelectedView />`
  useLayoutEffect(() => {
    /* At sites level, API returns all files as the search is by client_id and all files have it,
     * this could be useful in the future but for now we only show the relevant ones */
    if (inView([SITES], pathname)) {
      setEntityFiles((files || []).filter(file => ENTITY_KEYS_FROM_SITES.every(key => !file[key])));
    } else {
      setEntityFiles(files);
    }
  }, [files, pathname]);

  useLayoutEffect(() => {
    setCustomFolders(folders);
  }, [folders, pathname]);

  useLayoutEffect(() => {
    if (inView([SITES], pathname)) {
      setMapSites(data);
      setEntities(data);
    } else {
      setEntities(data);
    }
    setHoveredItem(null);
  }, [data, pathname]);

  useEffect(() => {
    if (inView([BUILDINGS], pathname) && Object.keys(site).length > 0) {
      setMapSites([site]);
    }
  }, [site, pathname]);

  useEffect(() => {
    if (inView([FLOORS], pathname) && siteUnits?.length > 0 && data.length > 0) {
      const currentFloors = (data || []).map(floor => floor.id);
      const currentUnits = siteUnits.filter(unit => currentFloors.includes(unit.floor_id));

      // if there are floors that are not referenced by any of the currentUnits, it means that the floor is unitless.
      const unitlessFloors = data.filter(floor => {
        const floorWithoutUnits = currentUnits.every(unit => {
          return unit.floor_id != floor.id;
        });
        return floorWithoutUnits;
      });

      const unitsToDisplay = currentUnits.concat(unitlessFloors);
      setCurrentUnits(unitsToDisplay);
    }
    if (inView([UNITS], pathname)) {
      setCurrentUnits(data);
    }
    if (inView([ROOMS], pathname)) {
      setCurrentUnits([unit]);
    }
  }, [data, unit, siteUnits, pathname]);

  const onClickCustomFolder = customFolder => {
    history.push(C.URLS.CUSTOM_FOLDERS(customFolder.id));
  };

  const onUploadFile = async event => {
    const [file] = event.target.files;
    try {
      showSnackbar({ message: `Uploading ${file.name}...`, severity: 'info' });
      const parentFilter: ParentQuery = query;
      await ProviderRequest.multipart(C.ENDPOINTS.FILE(), { ...parentFilter, file: event.target.files });
      showSnackbar({ message: `${file.name} uploaded`, severity: 'success' });
      reloadFiles();
    } catch (error) {
      showSnackbar({ message: `Error uploading ${file?.name || ''}: ${error}`, severity: 'error' });
      console.log('Error uploading the file', error);
    }
  };

  // We update now attributes, in the future we could just update the whole item
  const updateItem = async (
    currentItems,
    setNewItemsFunction,
    changedItem,
    attribute,
    endpoint: string,
    options = { successMessage: '' }
  ) => {
    const oldItems = [...currentItems];
    const updatedAttribute = { [attribute]: changedItem[attribute] };
    try {
      const newItems = currentItems.map(item => (item.id === changedItem.id ? { ...item, ...updatedAttribute } : item));
      setNewItemsFunction(newItems);
      await ProviderRequest.put(endpoint, updatedAttribute);
      if (options.successMessage) {
        showSnackbar({ message: options.successMessage, severity: 'success' });
      }
    } catch (error) {
      setNewItemsFunction(oldItems);
      showSnackbar({
        message: `Error setting ${attribute} to ${changedItem.name}: ${error}`,
        severity: 'error',
      });
      console.log(`Error setting ${attribute} to the item ${changedItem}:`, error);
    }
  };

  const onDownloadFile = async file => {
    const image = await ProviderRequest.getFiles(C.ENDPOINTS.FILE_DOWNLOAD(file.id), C.RESPONSE_TYPE.ARRAY_BUFFER);
    getFile(image, file.name, file.type);
  };

  const onDeleteItem = async ({ id, name, type }) => {
    try {
      const endpoint = type === CUSTOM_FOLDER_TYPE ? C.ENDPOINTS.FOLDER : C.ENDPOINTS.FILE;
      await ProviderRequest.delete(endpoint(id));
      if (type === CUSTOM_FOLDER_TYPE) {
        reloadCustomFolders();
      } else {
        reloadFiles();
      }
      showSnackbar({ message: `${name} deleted successfully`, severity: 'success' });
    } catch (error) {
      showSnackbar({ message: `Error deleting ${name}: ${error}`, severity: 'error' });
      console.log(`Error deleting the ${name}`, error);
    }
  };

  const onMoveToTrash = async ({ id, name, type }) => {
    try {
      const endpoint = type === CUSTOM_FOLDER_TYPE ? C.ENDPOINTS.FOLDER_TRASH : C.ENDPOINTS.FILE_TRASH;
      await ProviderRequest.put(endpoint(id), { deleted: true });
      if (type === CUSTOM_FOLDER_TYPE) {
        reloadCustomFolders();
      } else {
        reloadFiles();
      }
      showSnackbar({ message: `${name} deleted successfully`, severity: 'success' });
    } catch (error) {
      showSnackbar({ message: `Error deleting ${name}: ${error}`, severity: 'error' });
      console.log(`Error deleting the ${name}`, error);
    }
  };

  const onRestoreItem = async ({ id, name, type }) => {
    try {
      const endpoint = type === CUSTOM_FOLDER_TYPE ? C.ENDPOINTS.FOLDER_TRASH_RESTORE : C.ENDPOINTS.FILE_TRASH;
      await ProviderRequest.put(endpoint(id), { deleted: false });
      if (type === CUSTOM_FOLDER_TYPE) {
        reloadCustomFolders();
      } else {
        reloadFiles();
      }
      showSnackbar({ message: `${name} restored successfully`, severity: 'success' });
    } catch (error) {
      showSnackbar({ message: `Error restoring ${name}: ${error}`, severity: 'error' });
      console.log('Error restring the file', error);
    }
  };

  const onRenameItem = async (item, newName) => {
    const changedItem = { ...item, name: newName };
    const options = { successMessage: `${changedItem.name} renamed successfully` };
    if (changedItem.type === CUSTOM_FOLDER_TYPE) {
      updateItem(customFolders, setCustomFolders, changedItem, 'name', C.ENDPOINTS.FOLDER(changedItem.id), options);
    } else {
      updateItem(entityFiles, setEntityFiles, changedItem, 'name', C.ENDPOINTS.FILE(changedItem.id), options);
    }
  };

  const onConfirmRename = newName => {
    onRenameItem(showRenameDialog.item, newName);
    handleRenameDialogClose();
  };
  const onChangeTags = async changedItem => {
    if (changedItem.type === CUSTOM_FOLDER_TYPE) {
      updateItem(customFolders, setCustomFolders, changedItem, 'labels', C.ENDPOINTS.FOLDER(changedItem.id));
    } else if (isEntityFolder(changedItem)) {
      const entityEndpoints = {
        'folder-sites': () => C.ENDPOINTS.SITE(changedItem.id),
        'folder-buildings': () => C.ENDPOINTS.BUILDING(changedItem.id),
        'folder-floors': () => C.ENDPOINTS.FLOOR(changedItem.id),
        'folder-units': () => C.ENDPOINTS.UNIT(changedItem.id),
        'folder-rooms': () => C.ENDPOINTS.UNIT_AREAS(query.unit_id, changedItem.id),
      };
      const endpoint = entityEndpoints[changedItem.type]();
      updateItem(entities, setEntities, changedItem, 'labels', endpoint);
    } else {
      updateItem(entityFiles, setEntityFiles, changedItem, 'labels', C.ENDPOINTS.FILE(changedItem.id));
    }
  };

  const onPaste = async item => {
    const oldFiles = [...entityFiles];
    const oldFolders = [...customFolders];
    const isFolder = item.type === C.CUSTOM_FOLDER_TYPE;
    try {
      isFolder ? setCustomFolders([...customFolders, item]) : setEntityFiles([...entityFiles, item]);
      const parentInfo: ParentQuery & { parent_folder_id?: number } = query;
      if (isFolder && parentInfo.folder_id) {
        // For folders, BE uses this field for the parent
        parentInfo.parent_folder_id = parentInfo.folder_id;
        delete parentInfo.folder_id;
      }
      const endpoint = isFolder ? C.ENDPOINTS.FOLDER : C.ENDPOINTS.FILE;
      await ProviderRequest.put(endpoint(item.id), { ...parentInfo });
      showSnackbar({ message: `${item.name} successfully moved`, severity: 'success' });
      setItemInClipboard(null);
      isFolder ? reloadCustomFolders() : reloadFiles();
    } catch (error) {
      isFolder ? setCustomFolders(oldFolders) : setEntityFiles(oldFiles);
      showSnackbar({ message: `Error moving ${item.name}: ${error}`, severity: 'error' });
      console.log(`Error moving ${item.name}`, error);
    }
  };

  const areaData = parseBackendAreaData(netAreaData, pathname);
  const blob = new Blob([unitFloorPlanBlob], { type: 'image/png' });
  const floorPlanImageLocalLink = URL.createObjectURL(blob);

  const widgetData = {
    areaData,
    buildingId: getEntityId(hierarchy, 'building_id'),
    unitFloorPlan: floorPlanImageLocalLink,
    planId: getFloorPlanIdFromHierarchy(hierarchy),
    unitIds: getUnitIdsByView(entities, pathname, query),
  };

  const handleCreateNewFolderClick = React.useCallback(() => {
    setShowNewFolderDialog(true);
  }, []);

  const handleNewFolderDialogClose = React.useCallback(() => {
    setShowNewFolderDialog(false);
  }, []);

  const onAddComment = async (openedFile, comment) => {
    // @TODO: Optimistic update
    await ProviderRequest.post(C.ENDPOINTS.FILE_COMMENTS(openedFile.id), { comment });
    const fullFile = await ProviderRequest.get(C.ENDPOINTS.FILE(openedFile.id));
    const updatedFile = parseOpenedFile(fullFile);
    setOpenedFile(updatedFile);
  };

  const fileHandlers: FileHandlersType = {
    allowedUpload: !inView([TRASH], pathname), // This means we are inside a client -> @TODO: Ensure only DMS Admin/DMS Editor can create this
    onUploadFile: onUploadFile,
    onCreateFolder: handleCreateNewFolderClick,
    onMoveToTrash,
    onChangeTags,
    onDownload: onDownloadFile,
    onDelete: onDeleteItem,
    onRestore: onRestoreItem,
    onRename: handleRenameDialogOpen,
    onPaste: onPaste,
    onAddComment: onAddComment,
  };

  const handleNewFolderDialogAccept = React.useCallback(
    async folderName => {
      try {
        const parentInfo = inView([CUSTOM_FOLDER], pathname) ? { parent_folder_id: Number(query.folder_id) } : query;
        await ProviderRequest.post(C.ENDPOINTS.FOLDER(), { name: folderName, labels: [], ...parentInfo });
        reloadCustomFolders();
        showSnackbar({ message: `${folderName} folder created successfully`, severity: 'success' });
      } catch (error) {
        showSnackbar({
          message: `Error creating ${folderName} folder: ${error}`,
          severity: 'error',
        });
        console.log('Error creating the folder', error);
      }
      setShowNewFolderDialog(false);
    },
    [reloadCustomFolders, pathname, query]
  );

  return (
    <>
      <SelectedView
        data={entities}
        loadingState={loadingState}
        files={entityFiles}
        filter={filter}
        customFolders={customFolders}
        view={view}
        onClickFolder={onClickFolder}
        onClickCustomFolder={onClickCustomFolder}
        fileHandlers={fileHandlers}
        getEntityName={getEntityName}
        widgetData={widgetData}
        site={site}
        clientId={getUserClientId(hierarchy, query)}
        hierarchy={hierarchy}
      />

      {fileHandlers.allowedUpload && (
        <>
          <NewFolderDialog
            open={showNewFolderDialog}
            onClose={handleNewFolderDialogClose}
            onAccept={handleNewFolderDialogAccept}
          />
          <RenameDialog
            open={showRenameDialog.open}
            name={showRenameDialog.item?.name}
            label={showRenameDialog.label}
            onClose={handleRenameDialogClose}
            onRename={onConfirmRename}
          />
        </>
      )}
    </>
  );
}

export default DataView;
