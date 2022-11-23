import React from 'react';
import { FaSave as IconSave } from 'react-icons/fa';
import { LoadingIndicator } from 'archilyse-ui-components';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import ToolbarButton from '../toolbar-button/export';

import { MODE_IDLE, REQUEST_STATUS_BY_ACTION, RequestStatusType, SNACKBAR_DURATION_FOREVER } from '../../constants';
import { hasProjectChanged, isScaling } from '../../utils/export';
import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';
import { usePlanId } from '../../hooks/export';

const LOADING_STYLE = { width: 25, height: 25 };
const OPACITY_SAVED = 0.5;
const OPACITY_NEEDS_SAVING = 1;
function ToolbarSaveButton({ state, projectActions }) {
  const sceneRequestStatus = state.requestStatus[REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS];

  const planId = usePlanId();

  const onSaveProjectFailure = error => {
    let msg = 'Error occured while saving a project';
    if (error?.response?.data?.msg) {
      msg += `: ${error?.response?.data?.msg}`;
    }
    projectActions.showSnackbar({
      message: msg,
      severity: 'error',
    });
  };

  const saveProjectToFile = async e => {
    e.preventDefault();
    projectActions.showSnackbar({
      message: 'Saving, please wait...',
      severity: 'info',
      duration: SNACKBAR_DURATION_FOREVER,
    });
    await projectActions.saveProjectAsync(
      { planId, state, validated: true },
      { onFulfill: projectActions.onSaveProjectSuccessfull, onReject: onSaveProjectFailure }
    );
  };

  const isModifyingProject = state.mode !== MODE_IDLE || isScaling(state);
  const isLoading = sceneRequestStatus && sceneRequestStatus.status === RequestStatusType.PENDING;
  const projectHasChanges = hasProjectChanged(state);

  const saveStyle = { opacity: projectHasChanges && !isModifyingProject ? OPACITY_NEEDS_SAVING : OPACITY_SAVED };
  let tooltip = 'Project saved';
  if (isModifyingProject) tooltip = 'Cannot save while modifying the project';
  else if (projectHasChanges) tooltip = 'Save project';

  return (
    <ToolbarButton
      id="save-scene-button"
      active={false}
      tooltip={tooltip}
      onClick={saveProjectToFile}
      disabled={isLoading || !projectHasChanges || isModifyingProject}
    >
      {isLoading ? <LoadingIndicator style={LOADING_STYLE} /> : <IconSave style={saveStyle} />}
    </ToolbarButton>
  );
}

function mapStateToProps(state) {
  state = state['react-planner'];
  return {
    state,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(ToolbarSaveButton);
