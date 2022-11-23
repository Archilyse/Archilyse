import React, { useContext, useEffect, useState } from 'react';
import classNames from 'classnames';
import { ProviderLocalStorage, ProviderRequest } from 'Providers';
import { usePrevious, useRouter } from 'Common/hooks';
import { C } from 'Common';
import { Icon, SnackbarContext } from 'archilyse-ui-components';
import { Breadcrumb, LeftSidebar, Search } from 'Components';
import { useStore } from '../../hooks';
import { inView, parseOpenedFile } from '../../modules';
import { Actions } from '../../components';
import ContextMenu from './ContextMenu';
import Grid from './Grid';
import Table from './Table';
import LoadingData from './LoadingData';
import DetailsDrawer from './DetailsDrawer';
import ViewDrawer from './ViewDrawer';
import filterAndParseData from './modules/filterAndParseData';
import HeatmapDrawer from './HeatmapDrawer';
import EmptyData from './EmptyData';
import './selectedView.scss';

const FOLDER_ICON_COLOR = '#434C50';
const UPLOAD_ICON_COLOR = '#FEFEFE';

const { DMS_VIEWS } = C;
const { SITES, UNITS, ROOMS, ROOM, FLOORS, BUILDINGS, CUSTOM_FOLDER, TRASH, CLIENTS } = DMS_VIEWS;

const KEYDOWN = 'keydown';
const KEY_C = 'c';
const KEY_V = 'v';

const { VIEWS } = C;

const insideASite = pathname => inView([BUILDINGS, FLOORS, ROOMS, UNITS], pathname);
const insideAClient = pathname => inView([SITES, BUILDINGS, FLOORS, UNITS, ROOMS], pathname);

const isEmptyData = (pathname, files, customFolders, entities, isLoading) => {
  if (isLoading) return false;

  const areFilesOrFoldersEmpty = !files?.length && !customFolders?.length;

  // in custom folder or trash can not be entities, so we only check files and folders
  if (inView([CUSTOM_FOLDER, TRASH], pathname)) return areFilesOrFoldersEmpty;

  return !entities?.length && areFilesOrFoldersEmpty;
};

const renderContent = ({ pathname, files, customFolders, data, loadingState, view }, contentProps) => {
  const isLoading = loadingState.entities && loadingState.files && loadingState.folders;
  const showEmptyData = isEmptyData(pathname, files, customFolders, data, isLoading);
  const showTable = !isLoading && view === VIEWS.TABLE && !showEmptyData;
  const showGrid = !isLoading && view === VIEWS.DIRECTORY && !showEmptyData;

  if (isLoading) return <LoadingData />;
  if (showTable) return <Table {...contentProps} />;
  if (showGrid) return <Grid {...contentProps} />;
  if (showEmptyData) return <EmptyData onContextMenu={contentProps.onContextMenu} pathname={pathname} />;
};

const View = ({
  view,
  data,
  loadingState,
  files,
  filter,
  customFolders,
  site,
  onClickFolder,
  onClickCustomFolder,
  getEntityName,
  fileHandlers,
  widgetData,
  clientId,
  hierarchy,
}) => {
  const [contextMenu, setContextMenu] = useState({ top: null, left: null, clickedItem: null });
  const [detailsDrawer, setDetailsDrawer] = useState(false); // @TODO: This should not be in the state, it can be computed from the current pathname
  const { pathname, search } = useRouter();

  const itemInClipboard = useStore(state => state.itemInClipboard);
  const originalClipboardLocation = useStore(state => state.originalClipboardLocation);
  const openedFile = useStore(state => state.openedFile);
  const setOriginalClipboardLocation = useStore(state => state.setOriginalClipboardLocation);
  const hoveredItem = useStore(state => state.hoveredItem);
  const setHoveredItem = useStore(state => state.setHoveredItem);
  const setItemInClipboard = useStore(state => state.setItemInClipboard);
  const setOpenedFile = useStore(state => state.setOpenedFile);
  const currentUnits = useStore(state => state.currentUnits);
  const setFilter = useStore(state => state.setFilter);
  const setView = useStore(state => state.setView);

  const snackbar = useContext(SnackbarContext);

  const prevFiles = usePrevious(files);
  const pasteAllowed = itemInClipboard && search !== originalClipboardLocation;

  useEffect(() => {
    const sitesView = inView([SITES], pathname);

    const showDetailsDrawer = sitesView || insideASite(pathname);
    if (showDetailsDrawer) {
      setDetailsDrawer(true);
    }
    if (inView([TRASH, CLIENTS, CUSTOM_FOLDER, ROOM], pathname) && detailsDrawer) {
      setDetailsDrawer(false);
    }
  }, [pathname, site]);

  useEffect(() => {
    if (openedFile && detailsDrawer) {
      const isFileDeleted = !(files || []).find(file => file.id === openedFile.id);
      if (isFileDeleted) setDetailsDrawer(false);
    }
  }, [files, detailsDrawer, openedFile]);

  useEffect(() => {
    if (files !== prevFiles && openedFile) {
      setOpenedFile({ ...openedFile, ...files.find(file => file.id === openedFile.id) });
    }
  }, [files, openedFile, prevFiles]);

  const rawData = (data || []).map(d => ({ ...d }));
  const filteredData = filterAndParseData({
    entitiesData: rawData,
    areaData: widgetData.areaData,
    filter,
    getEntityName,
    customFolders,
    files,
    pathname,
    currentUnits,
  });

  const onClickDetails = React.useCallback(async selectedFile => {
    const fullFile = await ProviderRequest.get(C.ENDPOINTS.FILE(selectedFile.id));
    const openedFile = parseOpenedFile(fullFile);
    setOpenedFile(openedFile);
    setDetailsDrawer(true);
  }, []);

  const onCut = item => {
    setItemInClipboard(item);
    setOriginalClipboardLocation(search);
    snackbar.show({ message: `${item.name} copied in the clipboard`, severity: 'info' });
  };
  const onMouseEnter = item => {
    setHoveredItem(item);
  };

  const onMouseLeave = () => {
    setHoveredItem(null);
  };

  useEffect(() => {
    const handleKeyDown = event => {
      const { key, ctrlKey } = event;
      if (ctrlKey && key === KEY_C && hoveredItem) {
        onCut(hoveredItem);
      }
      if (ctrlKey && key === KEY_V && itemInClipboard) {
        fileHandlers.onPaste(itemInClipboard);
      }
    };
    window.addEventListener(KEYDOWN, handleKeyDown);
    return () => {
      window.removeEventListener(KEYDOWN, handleKeyDown);
    };
  }, [hoveredItem, fileHandlers.onPaste, itemInClipboard, onCut, pasteAllowed]);

  const contentProps = {
    onClickFolder,
    onClickCustomFolder,
    onMouseEnter,
    onMouseLeave,
    pathname,
    data: filteredData,
    itemInClipboard,
    onContextMenu: (event, clickedItem) => {
      event.preventDefault();
      if (clickedItem) event.stopPropagation();
      setContextMenu({ top: event.clientY, left: event.clientX, clickedItem });
    },
    onClickFile: onClickDetails,
    onChangeTags: fileHandlers.onChangeTags,
  };

  const closeContextMenu = () => {
    setContextMenu({ top: null, left: null, clickedItem: null });
  };

  const onHoverPieChartItem = id => {
    const item = contentProps.data?.find(d => Number(d.id) === Number(id));
    item ? onMouseEnter(item) : onMouseLeave();
  };

  const onFilterChange = value => {
    const filter = value.toLowerCase();
    setFilter(filter || '');
  };

  const onSwitchView = nextView => {
    ProviderLocalStorage.set(C.STORAGE.VIEW, nextView);
    setView(nextView);
  };

  const heatmapsDrawer = inView([UNITS, ROOMS], pathname);
  const viewDrawer = insideAClient(pathname) || insideASite(pathname);
  const additionalDrawers = detailsDrawer || viewDrawer;
  const selectedViewClass = classNames('selected-view', view, { compacted: additionalDrawers });

  return (
    <>
      <div className="main-layout">
        <div className="data-header">
          <div className="controls">
            <div className="data-header-navigation">
              <div className="breadcrumb">
                <Breadcrumb hierarchy={hierarchy} />
              </div>
              <Actions view={view} onSwitchView={onSwitchView} />
            </div>
            {filter !== null && filter !== undefined && (
              <Search
                initialValue={filter}
                onFilterChange={onFilterChange}
                delay={(data || []).length > 100 ? C.DELAY_FILTER_MS : 0}
              />
            )}

            {!inView([CLIENTS], pathname) && (
              <div className="folder-buttons">
                <div className="header-hseparator" />
                {fileHandlers.allowedUpload && (
                  <>
                    <div className="upload-button">
                      <label htmlFor="upload-file" className="button manage-file-button upload-file-button">
                        <Icon style={{ marginRight: '8px', marginLeft: '0px', color: UPLOAD_ICON_COLOR }}>upload</Icon>
                        Upload
                        <input id="upload-file" name="upload-file" type="file" onChange={fileHandlers.onUploadFile} />
                      </label>
                    </div>
                    <button
                      aria-label="add folder"
                      className="button manage-file-button"
                      onClick={fileHandlers.onCreateFolder}
                    >
                      <Icon style={{ marginRight: '8px', marginLeft: '0px', color: FOLDER_ICON_COLOR }}>addcircle</Icon>
                      Create folder
                    </button>

                    <div style={{ float: 'left' }}></div>
                    {pasteAllowed && (
                      <button
                        aria-label="paste"
                        className="button manage-file-button"
                        onClick={() => fileHandlers.onPaste(itemInClipboard)}
                      >
                        <Icon style={{ marginRight: '8px', marginLeft: '0px', fill: FOLDER_ICON_COLOR }}>paste</Icon>
                        Paste {itemInClipboard.type == C.CUSTOM_FOLDER_TYPE ? 'folder' : 'file'}
                      </button>
                    )}
                  </>
                )}
              </div>
            )}
            <div className="header-hseparator" />
          </div>
        </div>

        <div className={selectedViewClass}>
          <LeftSidebar pathname={pathname} clientId={clientId} />
          <>{renderContent({ pathname, files, customFolders, data, loadingState, view }, contentProps)}</>
        </div>
      </div>

      <div className="right-sidebar">
        {additionalDrawers && (
          <div className="widgets-container">
            {viewDrawer && <ViewDrawer {...widgetData} />}
            {heatmapsDrawer && (
              <HeatmapDrawer unitIds={widgetData.unitIds} planId={widgetData.planId} key={pathname} siteId={site?.id} />
            )}
            {detailsDrawer && (
              <DetailsDrawer
                areaData={widgetData.areaData}
                isAreaDataLoading={loadingState.areaData}
                onHoverPieChartItem={onHoverPieChartItem}
                details={openedFile}
                onChange={fileHandlers.onChangeTags}
                onDownload={fileHandlers.onDownload}
                onRenameFile={fileHandlers.onRename}
                onDelete={fileHandlers.onMoveToTrash}
                onAddComment={fileHandlers.onAddComment}
              />
            )}
          </div>
        )}
        <ContextMenu
          open={!!contextMenu.top}
          onClose={closeContextMenu}
          clickedItem={contextMenu.clickedItem}
          itemInClipboard={itemInClipboard}
          pasteAllowed={pasteAllowed}
          pathname={pathname}
          handlers={{ ...fileHandlers, onClickDetails, onCut }}
          anchorPosition={contextMenu}
        />
      </div>
    </>
  );
};

export default View;
