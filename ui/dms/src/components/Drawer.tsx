import React, { useEffect, useState } from 'react';
import cn from 'classnames';
import ReactDOM from 'react-dom';
import SideBarButton from './SideBarButton';
import './drawer.scss';

const Drawer = ({ collapsable = true, children }) => {
  const [collapsed, setCollapsed] = useState(true);
  const [node, setNode] = useState(null);

  useEffect(() => {
    setNode(document.getElementById('left-sidebar'));
  }, [node]);

  if (!node) return null;

  return ReactDOM.createPortal(
    <div className={cn('left-sidebar-container', { collapsed })}>
      {collapsable && (
        <div onClick={() => setCollapsed(!collapsed)}>
          <SideBarButton title={''} icon={'menu'} active={true} collapsed={collapsed} />
        </div>
      )}
      {children}
    </div>,
    node
  );
};

export default Drawer;
