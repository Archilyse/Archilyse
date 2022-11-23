import React, { useEffect, useRef, useState } from 'react';
import classnames from 'classnames';
import { Tooltip } from '@material-ui/core';
import './widget.scss';

const SLIDE_OFFSET = 80;

const CollapseButton = ({ collapsed, onClick }) => {
  const handleClick = event => {
    // prevent from changing a tab together with toggling collapse state
    event.stopPropagation();

    onClick();
  };

  return (
    <Tooltip title={collapsed ? 'Expand' : 'Collapse'}>
      <div className="collapse-widget-button" onClick={handleClick}>
        <p>{collapsed ? '<' : '>'}</p>
      </div>
    </Tooltip>
  );
};

const Tabs = ({ headers, children, onCollapse, collapsed, tab = 0, onChangeTab, extraContent }) => {
  const selectedChild = children.find((component, index) => (collapsed ? index === 0 : index === tab));

  const isTabSelected = (tab, index) => (collapsed ? index === 0 : tab === index);

  const tabs = collapsed ? headers.slice(0, 1) : headers;
  return (
    <div className="tabs">
      <div className="tab-headers">
        {tabs.map((tabName, index) => (
          <div
            key={tabName}
            className={`tab ${isTabSelected(tab, index) ? 'selected' : ''}`}
            onClick={() => onChangeTab(index)}
          >
            {isTabSelected(tab, index) && onCollapse && <CollapseButton onClick={onCollapse} collapsed={collapsed} />}
            <div className="name">{tabName}</div>
            {extraContent[index]}
          </div>
        ))}
      </div>
      <div className={classnames('tab-content', { collapsed })}>{selectedChild}</div>
    </div>
  );
};

const getStyle = (widget, fixedWidth, collapsed) => {
  if (!widget) return { width: fixedWidth };

  const { right } = widget.getBoundingClientRect();
  const width = collapsed ? SLIDE_OFFSET : fixedWidth;
  const x = collapsed ? window.innerWidth - right : 0;

  return { width, transform: `translateX(${x}px)` };
};

const Widget = ({
  collapsed: defaultCollapsed = false,
  onCollapse = null,
  onTabChange = null,
  className = '',
  children,
  tabHeaders,
  initialTab = 0,
  width = '100%',
  extraContent = [],
}) => {
  const [tab, setTab] = useState(initialTab);
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [style, setStyle] = useState({ width });
  const widget = useRef();

  const handleChangeTab = (index: number) => {
    setTab(index);

    if (onTabChange) onTabChange(index);
  };

  const handleCollapse = () => {
    setStyle(getStyle(widget.current, width, !collapsed));
    setCollapsed(!collapsed);
    onCollapse();
  };

  useEffect(() => {
    setTab(initialTab);
  }, [initialTab]);

  useEffect(() => {
    setCollapsed(defaultCollapsed);
  }, [defaultCollapsed]);

  const filteredChildren = React.Children.toArray(children);
  const classes = classnames('widget-drawer', className, { collapsed });

  return (
    <div data-testid="widget" ref={widget} style={style} className={classes}>
      <Tabs
        headers={tabHeaders}
        tab={tab}
        onCollapse={onCollapse ? handleCollapse : null}
        onChangeTab={handleChangeTab}
        collapsed={collapsed}
        extraContent={extraContent}
      >
        {filteredChildren}
      </Tabs>
    </div>
  );
};

export default Widget;
