import React from 'react';
import { FORM_LENGTH_STYLE } from '../../../shared-style.js';
import { PAGE_SIZES } from '../../../constants';

const { FIELD_LAYOUT, INPUT } = FORM_LENGTH_STYLE;

const PageSpecs = ({ scaleAllowed, scaleRatio, paperFormat, projectActions }) => {
  const onChangePaperFormat = newFormat => projectActions.setSceneProperties({ paperFormat: newFormat });
  const onChangeRatio = newRatio => projectActions.setSceneProperties({ scaleRatio: newRatio });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-around' }}>
      <h3>Page specs</h3>

      <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ ...FIELD_LAYOUT, width: '100%' }}>
          <select
            disabled={!scaleAllowed}
            id="paperFormat"
            name="paperFormat"
            style={{ backgroundColor: 'white', width: '80%' }}
            onChange={e => onChangePaperFormat(e.target.value)}
            defaultValue={'notSelected'}
            value={paperFormat}
          >
            <option key={'notSelected'} value={''}>
              Format
            </option>
            {Object.keys(PAGE_SIZES).map(pageSize => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>
        </div>
        <div style={FIELD_LAYOUT}>
          {/* @TODO: Use a different dropdown */}
          <h4>1:</h4>
          <input
            disabled={!scaleAllowed}
            id="scaleRatio"
            style={INPUT}
            name="scaleRatio"
            data-testid="scaleRatio"
            type="number"
            min={1}
            onChange={e => onChangeRatio(parseInt(e.target.value, 10))}
            value={scaleRatio}
          />
        </div>
      </div>
    </div>
  );
};

export default PageSpecs;
