import React from 'react';

import { RESCALE_NOT_ALLOWED_MESSAGE, SCALING_REQUIRED_MEASUREMENT_COUNT } from '../../../constants';
import { Background, XYCoord } from '../../../types';
import ScaleMeasurement from '../../../types/ScaleMeasurement';
import { isLine, isPolygon } from '../../../utils/geometry';
import { calculateScaleFactorFromPageSpecs, getAverageScaleFactor, needsRepeating } from './utils';

type ActionButtonsProps = {
  background: Background;
  scaleAllowed: boolean;
  scaleRatio: number;
  paperFormat: string;
  measurements: ScaleMeasurement[];
  onSaveMeasure: () => void;
  onSaveScale: (scale: number, options?: { withScaleRatio: boolean }) => void;
  onClear: () => void;
  points: XYCoord[];
};

const ACTION_BUTTONS_LAYOUT = {
  display: 'flex',
  flexDirection: 'column' as const,
  alignItems: 'center',
  justifyContent: 'space-around',
  marginTop: '20px',
  marginBottom: '20px',
};

const drawingStarted = points => isLine(points) || isPolygon(points);
const needMoreMeasures = measurements => measurements.length < SCALING_REQUIRED_MEASUREMENT_COUNT;

const getPageSpecsButtons = ({ scaleDiffers, hasMeasurements, scaleFromMeasures, scaleFromPageSpecs, onSaveScale }) => {
  return (
    <>
      <button className="primary-button" onClick={() => onSaveScale(scaleFromPageSpecs, { withScaleRatio: true })}>
        Validate scale using format/ratio
      </button>
      {scaleDiffers && hasMeasurements && (
        <div style={{ padding: 0 }}>
          <p>Please note that scale from measure is different from the page specs one:</p>
          <ul>
            <li style={{ marginTop: '10px' }}>From measure: {scaleFromMeasures.toFixed(1)}</li>
            <li style={{ color: 'red', marginTop: '10px' }}>From page specs: {scaleFromPageSpecs.toFixed(1)}</li>
          </ul>
        </div>
      )}
    </>
  );
};

const getMeasurementsButtons = ({ measurements, points, onClear, onSaveMeasure }) => {
  if (needsRepeating(measurements)) {
    return (
      <button className="secondary-button" style={{ marginTop: '10px' }} onClick={onClear}>
        Repeat current measurement
      </button>
    );
  }
  if (needMoreMeasures(measurements)) {
    return (
      <>
        <button className="primary-button" disabled={!drawingStarted(points)} onClick={onSaveMeasure}>
          Save measure
        </button>
        <button className="secondary-button" style={{ marginTop: '10px' }} onClick={onClear}>
          Clear
        </button>
      </>
    );
  }

  return null;
};

const ActionButtons = ({
  background,
  scaleAllowed,
  scaleRatio,
  paperFormat,
  measurements = [],
  onSaveMeasure,
  onSaveScale,
  onClear,
  points,
}: ActionButtonsProps) => {
  const hasMeasurements = measurements.length > 0;
  const hasPageSpecs = paperFormat && scaleRatio;

  const scaleFromPageSpecs = hasPageSpecs && calculateScaleFactorFromPageSpecs(scaleRatio, paperFormat, background);
  const scaleFromMeasures = getAverageScaleFactor(measurements);
  const scaleDiffers =
    hasPageSpecs && hasMeasurements && scaleFromPageSpecs.toFixed(1) !== scaleFromMeasures.toFixed(1);

  let buttons;

  if (!scaleAllowed) {
    buttons = (
      <button className="primary-button" disabled={true}>
        {RESCALE_NOT_ALLOWED_MESSAGE}
      </button>
    );
  } else if (!drawingStarted(points) && !hasMeasurements && !hasPageSpecs) {
    buttons = null;
  } else if (hasPageSpecs) {
    buttons = getPageSpecsButtons({
      hasMeasurements,
      scaleDiffers,
      scaleFromMeasures,
      scaleFromPageSpecs,
      onSaveScale,
    });
  } else if (drawingStarted(points) || hasMeasurements) {
    buttons = getMeasurementsButtons({ measurements, points, onClear, onSaveMeasure });
  }

  return <div style={{ ...ACTION_BUTTONS_LAYOUT }}>{buttons}</div>;
};

export default ActionButtons;
