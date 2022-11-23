import React from 'react';
import { Icon } from 'archilyse-ui-components';
import { Menu, MenuItem } from '@material-ui/core';
import { inView } from 'Components/DataView/modules';
import { C } from 'Common';
import { File, Folder } from 'Common/types';
import './contextMenu.scss';

const { TRASH } = C.DMS_VIEWS;
const MAX_NAME_LENGTH = 30;
const RIGHT_CLICK = 2;

const getTruncatedName = item =>
  item.name.length > MAX_NAME_LENGTH ? `${item.name.substring(0, MAX_NAME_LENGTH)}...` : item.name;

type AnchorPositionType = {
  top: number;
  left: number;
};

type ContextProps = {
  open: boolean;
  clickedItem: File | Folder;
  itemInClipboard: File | Folder;
  pathname: string;
  handlers: any; //@TODO: Todo
  pasteAllowed: boolean;
  onClose(event: React.SyntheticEvent): void;
  anchorPosition?: AnchorPositionType;
};

const ContextMenu = ({
  open,
  onClose,
  anchorPosition,
  pathname,
  clickedItem,
  itemInClipboard,
  pasteAllowed,
  handlers,
}: ContextProps) => {
  let optionalProps;
  if (anchorPosition && anchorPosition.top && anchorPosition.left) {
    optionalProps = {
      anchorPosition,
    };
  }

  const getActions = clickedItem => {
    if (!clickedItem) {
      if (pasteAllowed && itemInClipboard) {
        return [
          {
            name: `Paste ${getTruncatedName(itemInClipboard)} here`,
            onClick: () => handlers.onPaste(itemInClipboard),
            icon: <Icon>paste</Icon>,
          },
        ];
      }
      return [{ name: 'No contextual actions', onClick: () => {}, icon: <Icon>info</Icon> }];
    }

    if (inView([TRASH], pathname)) {
      return [
        { name: 'Restore', onClick: () => handlers.onRestore(clickedItem), icon: <Icon>restore</Icon> },
        { name: 'Delete permanently', onClick: () => handlers.onDelete(clickedItem), icon: <Icon>delete</Icon> },
      ];
    }

    if (clickedItem.type === C.CUSTOM_FOLDER_TYPE) {
      return [
        { name: 'Cut', onClick: () => handlers.onCut(clickedItem), icon: <Icon>cut</Icon> },
        { name: 'Rename', onClick: () => handlers.onRename(clickedItem), icon: <Icon>edit</Icon> },
        {
          name: 'Delete',
          onClick: () => handlers.onMoveToTrash(clickedItem),
          icon: <Icon>delete</Icon>,
        },
      ];
    }
    return [
      { name: 'Cut', onClick: () => handlers.onCut(clickedItem), icon: <Icon>cut</Icon> },
      { name: 'Details', onClick: () => handlers.onClickDetails(clickedItem), icon: <Icon>info</Icon> },
      { name: 'Download', onClick: () => handlers.onDownload(clickedItem), icon: <Icon>download</Icon> },
      { name: 'Rename', onClick: () => handlers.onRename(clickedItem), icon: <Icon>edit</Icon> },
      {
        name: 'Delete',
        onClick: () => handlers.onMoveToTrash(clickedItem),
        icon: <Icon>delete</Icon>,
      },
    ];
  };

  const actions = getActions(clickedItem);
  const onActionClick = handler => event => {
    onClose(event);
    handler();
  };

  return (
    <div
      className="context-menu"
      onMouseDownCapture={e => {
        // Material UI adds a modal when menu is visible, this closes it.
        if (e.button === RIGHT_CLICK) onClose(e);
      }}
    >
      <Menu
        disablePortal
        open={open}
        keepMounted
        transitionDuration={0}
        autoFocus={false}
        onClose={onClose}
        anchorReference="anchorPosition"
        PopoverClasses={{ root: 'context-menu-root' }}
        {...optionalProps}
      >
        {actions.map(action => (
          <MenuItem key={action.name} onClick={onActionClick(action.onClick)}>
            {action.icon ? (
              <div data-testid="context-menu-action" className="context-menu-action-icon">
                {action.icon}
              </div>
            ) : null}
            {action.name}
          </MenuItem>
        ))}
      </Menu>
    </div>
  );
};

export default ContextMenu;
