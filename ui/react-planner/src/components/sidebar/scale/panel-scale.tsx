import React, { useState } from 'react';
import { batch, connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import PanelScaleProps from '../../../types/PanelScaleProps';
import ScaleMeasurement from '../../../types/ScaleMeasurement';
import { REQUEST_STATUS_BY_ACTION, SCALING_REQUIRED_MEASUREMENT_COUNT } from '../../../constants';
import { objectsMap } from '../../../utils/objects-utils';
import { planActions, projectActions } from '../../../actions/export';
import { usePlanId } from '../../../hooks/export';
import projectHasAnnotations from '../../../utils/project-has-annotations';
import { getAverageScaleFactor, getPointsFromScaleToolLines, needsRepeating } from './utils';
import ScaleMeasurements from './scale-measurements';
import Panel from './../panel';
import PageSpecs from './page-specs';
import MeasureInput from './measure-input';
import ActionButtons from './action-buttons';

const contentArea: any = {
  height: 'auto',
  overflowY: 'auto',
  padding: '0.25em 1.15em',
  cursor: 'pointer',
  marginBottom: '1em',
  userSelect: 'none',
};

const Instructions = () => (
  <div style={{ padding: '20px' }}>
    <h3>Take {SCALING_REQUIRED_MEASUREMENT_COUNT} measures or set page specs</h3>
  </div>
);

const PanelScale = ({
  points,
  background,
  paperFormat,
  scaleRatio,
  scaleTool,
  floorScales,
  floorScalesRequest,
  stateExtractor,
  planActions,
  scaleArea,
  projectActions,
  scaleAllowed,
}: PanelScaleProps) => {
  const planId = usePlanId();

  const { distance, areaSize } = scaleTool;
  const [measurements, setMeasurements] = useState<ScaleMeasurement[]>([]);

  const showRepeatMeasure = () => {
    projectActions.showSnackbar({
      message: `Measurement differs too much from the previous one, please repeat it`,
      severity: 'error',
      duration: 2000,
    });
  };

  const showContinueMessage = measurements => {
    projectActions.showSnackbar({
      message: `Scale measurement #${measurements.length} taken, ${
        SCALING_REQUIRED_MEASUREMENT_COUNT - measurements.length
      } to go.`,
      severity: 'success',
      duration: 2000,
    });
  };

  const incrementMeasurement = () => {
    const lastMeasurement = {
      distance: distance,
      areaSize: parseFloat(areaSize),
      points: points,
      area: scaleArea,
    };
    return [...measurements, lastMeasurement];
  };

  const onSaveMeasure = () => {
    const measurements = incrementMeasurement();
    setMeasurements(measurements);
    if (needsRepeating(measurements)) {
      showRepeatMeasure();
    } else {
      const scaleFromMeasures = getAverageScaleFactor(measurements);
      batch(() => {
        planActions.setPlanScale(scaleFromMeasures); // So next measurements use this scale

        showContinueMessage(measurements);
        clearDrawing();
      });

      if (measurements.length === SCALING_REQUIRED_MEASUREMENT_COUNT) {
        onSaveScale(scaleFromMeasures);
      }
    }
  };

  const onSaveScale = async (scale: number, { withScaleRatio } = { withScaleRatio: false }) => {
    await projectActions.saveScale(
      { planId, scale, stateExtractor, withScaleRatio },
      {
        onFulfill: () => {
          projectActions.showSnackbar({ message: 'Plan scale set', severity: 'success', duration: 2000 });
          clearDrawing();
          projectActions.disableScaling();
          projectActions.setProjectHashCode();
        },
        onReject: () => {
          projectActions.showSnackbar({ message: 'Error occured while setting the plan scale', severity: 'error' });
        },
      }
    );
  };

  const clearDrawing = () => {
    projectActions.clearScaleDrawing();
    if (needsRepeating(measurements)) {
      setMeasurements(measurements.slice(0, -1)); // Erase last element
    }
  };

  return (
    <Panel name={'Scale mode'} opened={true}>
      <div style={contentArea} onWheel={e => e.stopPropagation()}>
        <Instructions />
        <hr />
        <>
          <MeasureInput projectActions={projectActions} distance={distance} areaSize={areaSize} points={points} />
          <br />
          <ScaleMeasurements
            floorScales={floorScales}
            floorScalesRequest={floorScalesRequest}
            scaleTool={scaleTool}
            measurements={measurements}
          />
          <br />
        </>
        <hr />
        <>
          <br />
          <PageSpecs
            projectActions={projectActions}
            paperFormat={paperFormat}
            scaleAllowed={scaleAllowed}
            scaleRatio={scaleRatio}
          />
          <br />
        </>
        <hr />
        <ActionButtons
          background={background}
          paperFormat={paperFormat}
          scaleRatio={scaleRatio}
          scaleAllowed={scaleAllowed}
          points={points}
          measurements={measurements}
          onSaveMeasure={onSaveMeasure}
          onSaveScale={onSaveScale}
          onClear={clearDrawing}
        />
      </div>
    </Panel>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const layerID = state.scene.selectedLayer;
  const layer = state.scene.layers[layerID];

  const { scaleTool, floorScales } = state;
  const { paperFormat, scaleRatio, background } = state.scene;

  const floorScalesRequest = state.requestStatus[REQUEST_STATUS_BY_ACTION.FETCH_FLOOR_SCALES];
  const scaleAllowed = !projectHasAnnotations(state);
  const points = getPointsFromScaleToolLines(state);
  const scaleArea = Object.values(layer.areas).find((a: any) => a.isScaleArea);

  return {
    background,
    paperFormat,
    scaleRatio,
    scaleTool,
    points,
    floorScales,
    floorScalesRequest,
    scaleAllowed,
    scaleArea,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { planActions, projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(PanelScale);
