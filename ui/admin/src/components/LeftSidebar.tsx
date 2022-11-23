import React from 'react';
import Drawer from './Drawer';
import './leftSidebar.scss';

const LeftSidebar = ({ buttons, bottomContent }) => {
  return (
    <Drawer>
      <div className="selected-view-left-sidebar">
        <header>
          <h4>Document Management System</h4>
          <p>Receive, track, manage and store digital documents.</p>
        </header>

        <div className="sidebar-buttons">{buttons}</div>

        <div className="sidebar-navigation-container">{bottomContent}</div>
      </div>
    </Drawer>
  );
};

export default LeftSidebar;
