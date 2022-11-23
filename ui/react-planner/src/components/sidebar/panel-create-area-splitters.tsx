import React from 'react';

import { ProviderRequest } from 'archilyse-ui-components';

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';
import { ENDPOINTS } from '../../constants';
import { usePlanId } from '../../hooks/export';
import Panel from './panel';

const UL_STYLE = { paddingRight: '20px', paddingLeft: '20px', marginTop: '10px' };

const PanelCreateAreaSplittersComponent = ({ projectActions }) => {
  const planId = usePlanId();

  function createAreaSplitters() {
    loadAnnotationWithAreaSplitters(planId, projectActions);
  }

  return (
    <Panel name={'Create Area Splitters'} opened={false}>
      <div style={UL_STYLE}>
        <button
          style={{ marginTop: '10px', whiteSpace: 'nowrap', marginBottom: '10px', width: '80%' }}
          className="primary-button"
          onClick={createAreaSplitters}
        >
          Create Kitchen Area Splitters
        </button>
      </div>
    </Panel>
  );
};

export async function loadAnnotationWithAreaSplitters(planId, projectActions) {
  try {
    const result = await ProviderRequest.get(ENDPOINTS.CREATE_AREA_SPLITTERS(planId));
    projectActions.loadProject(result);
    projectActions.reGenerateAreas();
    projectActions.showSnackbar({
      message: 'Area splitters created successfully',
      severity: 'success',
      duration: 2000,
    });
  } catch (error) {
    projectActions.showSnackbar({
      message: `Error when creating area splitters: ${error}`,
      severity: 'error',
    });
  }
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export const PanelCreateAreaSplitters = connect(null, mapDispatchToProps)(PanelCreateAreaSplittersComponent);
