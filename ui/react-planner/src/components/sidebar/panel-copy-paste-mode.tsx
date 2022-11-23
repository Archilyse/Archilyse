import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { objectsMap } from '../../utils/objects-utils';
import hasCopyPasteFromAnotherPlan from '../../utils/has-copy-paste-from-another-plan';
import hasCopyPasteBeenDragged from '../../utils/has-copy-paste-been-dragged';
import { copyPasteActions } from '../../actions/export';
import { usePlanId } from '../../hooks/export';
import Panel from './panel';

const H3_REGULAR_STYLE: any = { fontWeight: 'normal' };
const H3_HIGHLIGHT: any = { fontWeight: 'bold', fontSize: '14px' };

const STYLE_KEYBOARD = {
  color: '#fff',
  padding: '0.1em 0.3em',
  fontSize: 'inherit',
  fontWeight: 'normal',
} as any;

type PanelCopyPasteModeProps = {
  isDrawing: boolean;
  hasBeenDragged: boolean;
  hasBeenStarted: boolean;
  copyPasteActions: any;
};

const PanelCopyPasteMode = React.memo(
  ({ isDrawing, hasBeenDragged, hasBeenStarted, copyPasteActions }: PanelCopyPasteModeProps) => {
    const planId = usePlanId();

    const onClickSave = () => {
      copyPasteActions.saveCopyPasteSelection();
    };

    const step1 = isDrawing;
    const step2 = !isDrawing && !hasBeenDragged && hasBeenStarted;
    const step3 = hasBeenDragged;

    return (
      <Panel name={'Copy & paste mode'} opened={true}>
        <div
          data-testid={'copy-paste-panel'}
          style={{
            display: 'flex',
            justifyContent: 'center',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '10px',
          }}
        >
          <h2>Copy {`&`} paste</h2>
          <p>This feature is in development and only visible for admins</p>
          {hasCopyPasteFromAnotherPlan(planId) ? (
            <>
              <h3>Copied annotations from other plan detected</h3>
              <h3>
                Press <kbd style={STYLE_KEYBOARD}>Ctrl + v</kbd> to paste them
              </h3>
            </>
          ) : (
            <>
              <ol>
                <li>
                  <h3 style={step1 ? H3_HIGHLIGHT : H3_REGULAR_STYLE}>Copy lines drawing a rectangle</h3>
                </li>
                <li>
                  <h3 style={step2 ? H3_HIGHLIGHT : H3_REGULAR_STYLE}>Drag the selection with the mouse</h3>
                </li>
                <li>
                  <h3 style={step3 ? H3_HIGHLIGHT : H3_REGULAR_STYLE}>
                    Paste it by pressing <kbd style={STYLE_KEYBOARD}>Ctrl + v</kbd> or clicking in the button below
                  </h3>
                </li>
              </ol>
              {hasBeenDragged && (
                <button className="primary-button" onClick={onClickSave}>
                  Paste selection
                </button>
              )}
              {(step2 || step3) && (
                <>
                  <p />
                  <hr style={{ width: '100%' }} />
                  <h3 style={{ marginBottom: 0 }}>To paste in a different plan:</h3>
                  <ol>
                    <li>
                      <h3 style={H3_REGULAR_STYLE}>Open the plan</h3>
                    </li>
                    <li>
                      <h3 style={H3_REGULAR_STYLE}>
                        Press <kbd style={STYLE_KEYBOARD}>Ctrl + v</kbd> there
                      </h3>
                    </li>
                  </ol>
                </>
              )}
            </>
          )}
        </div>
      </Panel>
    );
  }
);

function mapStateToProps(state) {
  state = state['react-planner'];
  const { startPosition, draggingPosition } = state.copyPaste.selection;
  const hasBeenDragged = hasCopyPasteBeenDragged(draggingPosition);
  const hasBeenStarted = startPosition && startPosition.x !== -1;
  return {
    isDrawing: state.copyPaste.drawing,
    hasBeenDragged,
    hasBeenStarted,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { copyPasteActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(PanelCopyPasteMode);
