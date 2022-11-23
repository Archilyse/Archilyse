import React from 'react';
import { capitalize, Icon } from 'archilyse-ui-components';
import { Fab } from '@material-ui/core/';
import './header.scss';

const Header = ({ title }) => {
  const headerTitle = title === '/profile' ? 'Settings' : capitalize(title.replace('/', ''));
  return (
    <div id="admin-header" className="header">
      <div className="dms-navbar">
        <span>{headerTitle}</span>
      </div>
      <div className="add-icon">
        <Fab aria-label="add">
          <Icon>plus</Icon>
        </Fab>
      </div>
    </div>
  );
};

export default Header;
