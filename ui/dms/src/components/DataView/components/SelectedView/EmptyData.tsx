import React from 'react';
import { Icon } from 'archilyse-ui-components';
import { C } from 'Common';
import { inView } from 'Components/DataView/modules';
import './emptyData.scss';

const { CUSTOM_FOLDER } = C.DMS_VIEWS;

const getMessageByView = pathname => {
  switch (pathname) {
    case C.DMS_VIEWS.ROOM:
      return `Empty Folder`;
    case C.DMS_VIEWS.SITES:
    case C.DMS_VIEWS.BUILDINGS:
    case C.DMS_VIEWS.FLOORS:
    case C.DMS_VIEWS.UNITS:
    case C.DMS_VIEWS.ROOMS:
    case C.DMS_VIEWS.CLIENTS:
      return `The ${pathname.replace('/', '')} are not processed`;
    case C.DMS_VIEWS.CUSTOM_FOLDER:
      return 'This folder is empty, upload a file or create a folder';
  }
};

const EmptyData = ({ onContextMenu, pathname }) => {
  const iconName = inView([CUSTOM_FOLDER], pathname) ? 'folder' : 'clear_all';
  const message = getMessageByView(pathname);

  return (
    <div className="c-empty-data" onContextMenu={event => onContextMenu(event, null)} data-testid="empty-data">
      <Icon style={{ fontSize: '100px', color: 'lightgray' }}>{iconName}</Icon>
      <p className="empty-data">{message}</p>
    </div>
  );
};

export default EmptyData;
