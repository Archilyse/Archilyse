import React, { useState } from 'react';
import { Tabs as MaterialTabs, Tab } from '@material-ui/core';
import './tabs.scss';

const TabPanel = props => {
  const isNotVisible = props.value !== props.index;
  return <div className={`tab-panel ${isNotVisible ? 'hidden' : ''}`}>{props.children}</div>;
};

const Tabs = ({ headers, children }) => {
  const [selectedTab, setTab] = useState(0);
  const handleChange = (event, newTab) => setTab(newTab);

  return (
    <>
      <MaterialTabs value={selectedTab} onChange={handleChange}>
        {headers.map(tabName => (
          <Tab key={tabName} label={tabName} />
        ))}
      </MaterialTabs>
      {children.map((component, index) => {
        return (
          <TabPanel key={index} value={selectedTab} index={index}>
            {component}
          </TabPanel>
        );
      })}
    </>
  );
};

export default Tabs;
