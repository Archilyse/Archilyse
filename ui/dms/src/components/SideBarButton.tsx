import React from 'react';
import { Icon } from 'archilyse-ui-components';
import cn from 'classnames';
import './sideBarButton.scss';

const SVG_STYLE = {
  width: 38,
  height: 30,
  fontSize: 28,
  marginLeft: 0,
  color: '#cccccc',
};

const SideBarButton = ({ title, icon, active, collapsed }) => {
  return (
    <div className={cn('row', { active, collapsed })} id={title ? '' : 'sliderButton'}>
      <div id="icon">
        <Icon
          style={{
            ...SVG_STYLE,
          }}
        >
          {icon}
        </Icon>
      </div>
      <div id="title">
        <span>{title}</span>
      </div>
    </div>
  );
};

export default SideBarButton;
