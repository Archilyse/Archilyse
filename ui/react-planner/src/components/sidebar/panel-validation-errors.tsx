import React from 'react';

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { ValidationError } from '../../types';
import { getValidationErrorColor } from '../../utils/export';
import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';
import Panel from './panel';

type PanelValidationErrorsProps = {
  errors: any;
  highlightedError: string;
  projectActions: any;
};

const PanelValidationErrors = ({ errors, highlightedError, projectActions }: PanelValidationErrorsProps) => {
  const errorList: ValidationError[] = errors;

  const onMouseEnter = errorObjectId => {
    projectActions.setHighlightedError(errorObjectId);
  };

  return (
    <Panel name={'Layout issues'} opened={true}>
      <ul>
        {errorList.map(({ object_id, type, text, is_blocking }, index) => (
          <li
            data-testid={`error-list-${index + 1}`}
            style={{ color: getValidationErrorColor(is_blocking, object_id, highlightedError), cursor: 'pointer' }}
            key={object_id}
            onMouseEnter={() => onMouseEnter(object_id)}
            onMouseLeave={() => onMouseEnter('')}
          >
            <p>{type}</p>
            <p style={{ color: 'white' }}>{text}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const errors = state.validationErrors;
  const highlightedError = state.highlightedError;
  return {
    errors,
    highlightedError,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(PanelValidationErrors);
