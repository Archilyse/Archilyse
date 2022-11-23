import React from 'react';
import { isPolygon } from '../../../utils/geometry';
import { FORM_LENGTH_STYLE } from '../../../shared-style.js';

const { LAYOUT, FIELD_LAYOUT, INPUT } = FORM_LENGTH_STYLE;

const MeasureInput = ({ distance, projectActions, points, areaSize }) => {
  const onChangeDistance = event => {
    const newDistance = event.target.value;
    projectActions.setScaleToolProperties({ distance: parseFloat(newDistance), userHasChangedMeasures: true });
  };

  const onChangeAreaSize = event => {
    const newAreaSize = event.target.value;
    projectActions.setScaleToolProperties({ areaSize: parseFloat(newAreaSize), userHasChangedMeasures: true });
  };

  const showAreaSize = isPolygon(points);
  const showDistance = !isPolygon(points); // Shown by default unless we are measuring a polygon

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-around' }}>
      <h3>Measures</h3>
      {showDistance && (
        <div style={LAYOUT}>
          <div style={FIELD_LAYOUT}>
            <label htmlFor="distance">Distance</label>
            <input
              id="distance"
              style={INPUT}
              name="distance"
              type="number"
              onChange={onChangeDistance}
              value={distance}
            />
            <label>m</label>
          </div>
        </div>
      )}
      {showAreaSize && (
        <div style={LAYOUT}>
          <div style={FIELD_LAYOUT}>
            <label htmlFor="area-size">Area size</label>
            <input
              id="area-size"
              style={INPUT}
              name="area-size"
              type="number"
              onChange={onChangeAreaSize}
              value={areaSize}
            />
            <label>
              m<sup>2</sup>
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

export default MeasureInput;
