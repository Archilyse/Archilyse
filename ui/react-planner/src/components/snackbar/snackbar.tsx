import { Snackbar } from 'archilyse-ui-components';
import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';

const SnackbarContainer = ({ snackbar, projectActions }: any) => {
  if (!snackbar) return null;

  return (
    <Snackbar
      {...snackbar}
      onClose={(event, reason: 'clickaway' | 'timeout' | 'escapeKeyDown') => {
        if (reason !== 'clickaway') {
          projectActions.closeSnackbar();
        }
      }}
    />
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const { snackbar } = state;
  return {
    snackbar,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(SnackbarContainer);
