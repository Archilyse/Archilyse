import React from 'react';
import FolderIcon from '@material-ui/icons/Folder';
import './emptyFolder.scss';

const EmptyFolder = ({ onContextMenu }) => {
  return (
    <div className="c-empty-folder" onContextMenu={event => onContextMenu(event, null)} data-testid="empty-folder">
      <FolderIcon />
      <p className="empty-folder">This folder is empty, upload a file or create a folder.</p>
    </div>
  );
};

export default EmptyFolder;
