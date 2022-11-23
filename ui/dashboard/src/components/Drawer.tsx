import React from 'react';
import './drawer.scss';

const SliderButton = ({ onClick, open }) => (
  <div className="drawer-button" onClick={onClick}>
    <div className="circle">
      <p>{open ? '<' : '>'}</p>
    </div>
  </div>
);

const Drawer = ({ open, onToggle = undefined, children }) => {
  return (
    <aside id={'drawer'} className={open ? '' : 'closed-drawer slide-left'}>
      {onToggle && <SliderButton open={open} onClick={onToggle} />}
      {children}
    </aside>
  );
};

export default Drawer;
