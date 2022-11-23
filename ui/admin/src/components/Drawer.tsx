import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import cn from 'classnames';
import './drawer.scss';

const SliderButton = ({ onClick, collapsed }) => (
  <div className={cn('drawer-button', { collapsed })} onClick={onClick}>
    <div className="circle">
      <p>{collapsed ? '>' : '<'}</p>
    </div>
  </div>
);

const Drawer = ({ collapsable = true, children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const node = document.getElementById('left-sidebar');

  if (!node) return null;

  return ReactDOM.createPortal(
    <div className={cn('left-sidebar-container', { collapsed })}>
      {collapsable && <SliderButton collapsed={collapsed} onClick={() => setCollapsed(!collapsed)} />}
      {!collapsed && children}
    </div>,
    node
  );
};

export default Drawer;
