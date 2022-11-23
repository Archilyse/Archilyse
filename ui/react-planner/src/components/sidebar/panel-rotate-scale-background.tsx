import React, { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { extractError } from 'archilyse-ui-components';
import { useCheckUnsavedChanges, usePlanId } from '../../hooks/export';
import { projectActions } from '../../actions/export';
import { objectsMap } from '../../utils/objects-utils';
import { Background } from '../../types';
import { FORM_LENGTH_STYLE } from '../../shared-style.js';
import { MODE_IDLE, SNACKBAR_DURATION_FOREVER } from '../../constants';
import Panel from './panel';

type InputProps = { background: Background; onChange: (args: any) => void };

const { LAYOUT, FIELD_LAYOUT, INPUT } = FORM_LENGTH_STYLE;

const originalBackground: Background = {
  width: 0,
  height: 0,
  rotation: 0,
  shift: {
    x: 0,
    y: 0,
  },
};

const parseFalsy = value => {
  if (value !== 0 && !value) return ''; // We want to return empty value so the user can delete the numeric input
  return Number(value);
};

const Dimensions = ({ backgroundScale, onChange }: { backgroundScale: number; onChange: InputProps['onChange'] }) => (
  <>
    <div style={FIELD_LAYOUT}>
      <label htmlFor="backgroundScale">Scale</label>
      <input
        id="backgroundScale"
        style={INPUT}
        name="backgroundScale"
        type="number"
        step={0.01}
        onChange={({ target }) => onChange(Number(target.value || 0))}
        value={backgroundScale}
      />
      <label>factor</label>
    </div>
  </>
);

const Shift = ({ background, onChange }: InputProps) => (
  <>
    <div style={FIELD_LAYOUT}>
      <label htmlFor="shiftX">Shift x</label>
      <input
        step="1"
        id="shiftX"
        style={INPUT}
        name="shiftX"
        type="number"
        onChange={({ target }) => onChange({ x: parseFalsy(target.value), y: background.shift.y })}
        value={background.shift?.x}
      />
      <label>px</label>
    </div>
    <br /> <p />
    <div style={FIELD_LAYOUT}>
      <label htmlFor="shiftY">Shift y</label>
      <input
        step="1"
        id="shiftY"
        style={INPUT}
        name="shiftY"
        type="number"
        onChange={({ target }) => onChange({ x: background.shift.x, y: parseFalsy(target.value) })}
        value={background.shift?.y}
      />
      <label>px</label>
    </div>
  </>
);

const Rotation = ({ background, onChange }: InputProps) => (
  <>
    <div style={FIELD_LAYOUT}>
      <label htmlFor="rotation">Rotation</label>
      <input
        step="0.5"
        id="rotation"
        style={INPUT}
        name="rotation"
        type="number"
        onChange={onChange}
        value={background.rotation || 0}
      />
      <label>dg</label>
    </div>
  </>
);

const PanelRotateScaleBackground = ({ state, background, floorplanWidth, floorplanHeight, projectActions }) => {
  const planId = usePlanId();
  const [backgroundScale, setBackgroundScale] = useState<number>(1);
  const [userHasUnsavedChanges, setUserHasUnsavedChanges] = useState<boolean>(false);
  const savedRef = React.useRef(userHasUnsavedChanges);

  React.useEffect(() => {
    savedRef.current = userHasUnsavedChanges;
  }, [userHasUnsavedChanges]);

  useEffect(() => {
    return () => {
      if (savedRef.current) {
        projectActions.showSnackbar({
          message: 'Rotate/scale background changes were not saved',
          severity: 'warning',
          duration: 3000,
        });
      }
    };
  }, []);

  useCheckUnsavedChanges(userHasUnsavedChanges);

  const onChangeDimensions = newScale => {
    setUserHasUnsavedChanges(true);
    setBackgroundScale(newScale);
    const newDimensions = {
      width: Math.floor(floorplanWidth * newScale),
      height: Math.floor(floorplanHeight * newScale),
    };
    projectActions.setBackgroundDimensions({ ...newDimensions });
  };

  const onChangeRotation = event => {
    setUserHasUnsavedChanges(true);
    const { value: newRotation = 0 } = event.target;
    projectActions.setBackgroundRotation({ rotation: Number(newRotation) });
  };

  const onChangeShift = (shift: Background['shift']) => {
    setUserHasUnsavedChanges(true);
    projectActions.setBackgroundShift({ shift });
  };

  const saveDefaultValues = () => {
    Object.assign(originalBackground, background);
  };

  const onSaveDimensions = async () => {
    setUserHasUnsavedChanges(false);
    await projectActions.saveProjectAsync(
      { planId, state, validated: true },
      {
        onFulfill: () => {
          projectActions.showSnackbar({
            message: 'New dimensions saved sucessfully',
            severity: 'success',
            duration: 3000,
          });
          saveDefaultValues();

          projectActions.setMode(MODE_IDLE);
          projectActions.setProjectHashCode();
        },
        onReject: error => {
          projectActions.showSnackbar({
            message: `Error saving dimensions: ${extractError(error)}`,
            severity: 'error',
            duration: SNACKBAR_DURATION_FOREVER,
          });
        },
      }
    );
  };

  const setInitialBackgroundScale = (originalBackgroundWidth, floorplanWidth) => {
    const backgroundScale = parseFloat((originalBackgroundWidth / floorplanWidth).toFixed(2));
    setBackgroundScale(backgroundScale);
  };

  const onReset = () => {
    const { width, height, rotation, shift } = originalBackground;
    projectActions.setBackgroundDimensions({ width, height });
    projectActions.setBackgroundRotation({ rotation });
    projectActions.setBackgroundShift({ shift });
    setInitialBackgroundScale(originalBackground.width, floorplanWidth);
  };

  useEffect(() => {
    setInitialBackgroundScale(originalBackground.width, floorplanWidth);
  }, [originalBackground.width, floorplanWidth]);

  useEffect(() => {
    // @TODO: This may fail if we enable the mode before loading the background image
    saveDefaultValues();

    return () => {
      onReset();
    };
  }, []);

  return (
    <Panel name={'Rotate/scale background'} opened={true}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '10px',
        }}
      >
        <div style={LAYOUT}>
          <Dimensions backgroundScale={backgroundScale} onChange={onChangeDimensions} />
          <br /> <p />
          <hr style={{ width: '100%' }} />
          <br /> <p />
          <Shift background={background} onChange={onChangeShift} />
          <hr style={{ width: '100%' }} />
          <br /> <p />
          <Rotation background={background} onChange={onChangeRotation} />
        </div>
        <br /> <p />
        <button className="primary-button" onClick={onSaveDimensions}>
          {'Save'}
        </button>
        <button className="secondary-button" style={{ marginTop: '10px' }} onClick={onReset}>
          Reset
        </button>
      </div>
    </Panel>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const background: Background = state.scene.background;
  const floorplanWidth = state.floorplanDimensions.width;
  const floorplanHeight = state.floorplanDimensions.height;
  return {
    state,
    background,
    floorplanWidth,
    floorplanHeight,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(PanelRotateScaleBackground);
