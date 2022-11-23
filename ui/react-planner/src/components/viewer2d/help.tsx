import React from 'react';
import { Modal } from '@material-ui/core';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { MODE_IDLE } from '../../constants';
import * as SharedStyle from '../../shared-style';

import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';

const STYLE_MODAL = {
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
} as any;

const STYLE_BLACK_DIALOG = {
  backgroundColor: SharedStyle.PRIMARY_COLOR.alt,
  color: SharedStyle.PRIMARY_COLOR.text_alt,
  outline: `solid 1px ${SharedStyle.PRIMARY_COLOR.text_alt}`,
  padding: '20px',
};
const STYLE_UL = { padding: '10px' };
const STYLE_LI = { margin: '10px', display: 'flex', justifyContent: 'space-between', width: '100%' };

const STYLE_KEYBOARD = {
  // Extracted from old editor
  border: '1px solid #aaa',
  borderRadius: '0.3em',
  boxShadow: '0.1em 0.1em 0.2em rgba(0, 0, 0, 0.1)',
  backgroundColor: '#f9f9f9',
  backgroundImage: 'linear-gradient(to bottom, #eee, #f9f9f9, #eee)',
  color: '#000',
  padding: '0.1em 0.3em',
  fontSize: 'inherit',
} as any;

const helpShortcuts = {
  General: [
    { key: 'Ctrl + s', help: 'Save project' },
    { key: 'Ctrl + x', help: 'Turn Off/On snapping' },
    { key: 'Ctrl + z', help: 'Undo last action' },
    { key: 'Escape', help: 'Unselect current selection' },
    { key: 'l', help: 'Open/close catalog' },
    { key: 'z', help: 'Fit to screen' },
    { key: 'Space', help: '(Hold) Hide annotations and show only the floorplan' },
    { key: 'Ctrl', help: '(Hold) Pan through the view' },
  ],
  Drawing: [
    { key: 'Ctrl + \u2192', help: 'Increase width of selected feature' },
    { key: 'Ctrl + \u2190', help: 'Decrease width of selected feature' },
    { key: 'Ctrl + \u2191', help: 'Increase height of selected feature' },
    { key: 'Ctrl + \u2193', help: 'Decrease height of selected feature' },
    { key: '+', help: 'Increase width of a wall' },
    { key: '-', help: 'Decrease width of a wall' },
    { key: 'f', help: 'Change the reference line of a wall' },
    { key: 'r', help: 'Rotate the selected door' },
    { key: 'Backspace/Delete', help: 'Delete selection' },
  ],
  'Copy paste': [{ key: 'Ctrl + v', help: 'Paste selection/Restore copied annotations from another plan' }],
};
const Help = ({ projectActions }) => {
  return (
    <Modal
      data-testid="help-modal"
      aria-labelledby="help-modal"
      aria-describedby="help-modal"
      open={true}
      onClose={() => projectActions.setMode(MODE_IDLE)}
      style={STYLE_MODAL}
    >
      <div style={STYLE_BLACK_DIALOG}>
        <h2>Help</h2>
        {Object.entries(helpShortcuts).map(([section, shortcuts]) => (
          <>
            <h3>{section}</h3>
            <ul style={STYLE_UL}>
              {shortcuts.map(shortcut => (
                <li key={shortcut.help} style={STYLE_LI}>
                  <kbd style={STYLE_KEYBOARD}>{shortcut.key}</kbd> {shortcut.help}
                </li>
              ))}
            </ul>
          </>
        ))}
      </div>
    </Modal>
  );
};

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(null, mapDispatchToProps)(Help);
