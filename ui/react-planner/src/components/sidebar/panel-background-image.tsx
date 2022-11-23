import React from 'react';
import Panel from './panel';

const PanelBackgroundImage = props => {
  return (
    <Panel name={'Background only'} opened={true}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '10px',
        }}
      >
        <h2>Showing floorplan only</h2>
        <h3>
          Release {'"'}
          <kbd>space</kbd>
          {'"'} to show annotations again
        </h3>
      </div>
    </Panel>
  );
};

export default PanelBackgroundImage;
