import React from 'react';
import { Tooltip } from '@material-ui/core';
import { C } from '../common';

const GoToPipelineRenderer = ({ data, enforceMasterPlan, thereIsAMasterPlan }) => {
  const disabled = enforceMasterPlan && !thereIsAMasterPlan;

  if (disabled)
    return (
      <Tooltip title={'Select a master plan in the building before start labelling'}>
        <div>Go to pipeline</div>
      </Tooltip>
    );
  return (
    <a href={C.URLS.EDITOR(data.id)} rel="noreferrer" target="_blank">
      Go to pipeline
    </a>
  );
};

export default GoToPipelineRenderer;
