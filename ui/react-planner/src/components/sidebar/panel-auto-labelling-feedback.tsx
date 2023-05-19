import React from 'react';
import { MdThumbDown, MdThumbUp } from 'react-icons/md';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { ProviderMetrics } from '../../providers';
import { PREDICTION_FEEDBACK_EVENTS } from '../../constants';
import { projectActions } from '../../actions/export';
import { objectsMap } from '../../utils/objects-utils';

import Panel from './panel';

const { PREDICTION_GOOD, PREDICTION_BAD } = PREDICTION_FEEDBACK_EVENTS;

const PanelAutoLabellingFeedback = ({ projectActions }) => {
  const onReportPrediction = (feedback: PREDICTION_FEEDBACK_EVENTS) => {
    projectActions.showSnackbar({
      message: 'Thanks! We will use the feedback to improve auto-labelling',
      severity: 'info',
      duration: 3000,
    });
    ProviderMetrics.trackPredictionFeedback(feedback);
    projectActions.toggleAutoLabellingFeedback();
  };
  return (
    <Panel name={'Auto-Labelling feedback'} opened={true}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '10px',
        }}
      >
        <h2>How is this auto-labelling result?</h2>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            width: '100%',
          }}
        >
          <MdThumbUp
            style={{ cursor: 'pointer' }}
            size={'1.5rem'}
            onClick={() => onReportPrediction(PREDICTION_GOOD)}
            data-testid={'thumbs-up'}
          />
          <MdThumbDown
            style={{ cursor: 'pointer' }}
            size={'1.5rem'}
            onClick={() => onReportPrediction(PREDICTION_BAD)}
            data-testid={'thumbs-down'}
          />
        </div>
      </div>
    </Panel>
  );
};

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(null, mapDispatchToProps)(PanelAutoLabellingFeedback);
