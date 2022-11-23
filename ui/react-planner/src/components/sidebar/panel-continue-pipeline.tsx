import React from 'react';
import { URLS } from '../../constants';
import { hasProjectChanged } from '../../utils/export';
import { usePlanId } from '../../hooks/export';

import Panel from './panel';

const PanelContinuePipeline = ({ state }) => {
  const planId = usePlanId();

  const projectHasChanges = hasProjectChanged(state);

  const onClick = () => {
    window.open(URLS.OLD_PIPELINE_CLASSIFICATION(planId), '_blank');
  };

  return (
    <Panel name={'Pipeline'} opened={true}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          padding: '10px',
        }}
      >
        <h3>{projectHasChanges ? 'Please save the plan to continue' : 'Plan labelled successfully'}</h3>
        <button className="primary-button" disabled={projectHasChanges} onClick={onClick}>
          Go to classification
        </button>
      </div>
    </Panel>
  );
};

export default PanelContinuePipeline;
