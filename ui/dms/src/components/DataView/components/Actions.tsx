import React from 'react';
import { Switch } from '@material-ui/core/';
import { C } from 'Common';
import './actions.scss';

const { VIEWS } = C;
const Actions = ({ view, onSwitchView }) => {
  const toggleView = () => (view === VIEWS.TABLE ? onSwitchView(VIEWS.DIRECTORY) : onSwitchView(VIEWS.TABLE));

  return (
    <div className="actions">
      <label>
        <span id="grid-view-title">Grid</span>
        <Switch
          checked={view === VIEWS.TABLE}
          size={'small'}
          className="toggle-view-switch"
          data-testid="toggle-view"
          onChange={() => toggleView()}
          name="toggleView"
        />
        <span id="table-view-title">Table</span>
      </label>
    </div>
  );
};

export default Actions;
