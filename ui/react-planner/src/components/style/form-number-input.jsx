import React, { useState, useEffect } from 'react';
import * as SharedStyle from '../../shared-style';
import { KEYBOARD_KEYS } from '../../constants';

const STYLE_INPUT = {
  display: 'block',
  width: '100%',
  padding: '0 2px',
  fontSize: '13px',
  lineHeight: '1.25',
  color: SharedStyle.PRIMARY_COLOR.input,
  backgroundColor: SharedStyle.COLORS.white,
  backgroundImage: 'none',
  border: '1px solid rgba(0,0,0,.15)',
  outline: 'none',
  height: '30px',
};

const FormNumberInput = ({
  value = 0,
  min = Number.MIN_SAFE_INTEGER,
  max = Number.MAX_SAFE_INTEGER,
  onChange,
  onValid = undefined,
  style = {},
  placeholder = undefined,
  propertyName,
  fixMinMaxOnlyOnNoFocus = false,
}) => {
  const [focus, setFocus] = useState(false);
  const [valid, setValid] = useState(true);
  const [showedValue, setShowedValue] = useState(value);

  const numericInputStyle = { ...STYLE_INPUT, ...style };

  if (focus) numericInputStyle.border = `1px solid ${SharedStyle.SECONDARY_COLOR.main}`;

  if ((fixMinMaxOnlyOnNoFocus && !focus) || !fixMinMaxOnlyOnNoFocus) {
    if (!isNaN(min) && isFinite(min) && showedValue < min) setShowedValue(min); // value = min;
    if (!isNaN(max) && isFinite(max) && showedValue > max) setShowedValue(max);
  }
  const saveFn = e => {
    e.stopPropagation();
    onChange({ target: { value: e.nativeEvent.target.value } });
  };

  useEffect(() => {
    if (value !== showedValue) setShowedValue(value);
  }, [value]);

  return (
    <>
      <div style={{ position: 'relative' }}>
        <input
          type="number"
          step="1"
          name={propertyName}
          value={showedValue}
          style={numericInputStyle}
          onChange={e => {
            const { value: inputValue } = e.nativeEvent.target;
            const valid = Number.isInteger(Number(inputValue));
            setShowedValue(inputValue);
            setValid(valid);
            const isNotEmpty = inputValue !== undefined && inputValue !== null && inputValue !== '';
            if (valid && isNotEmpty) {
              if (onValid) onValid(e.nativeEvent);
              saveFn(e);
            }
          }}
          onFocus={e => setFocus(true)}
          onBlur={e => setFocus(false)}
          onKeyDown={e => {
            if (e.key == KEYBOARD_KEYS.ENTER || e.key == KEYBOARD_KEYS.TAB) {
              saveFn(e);
            }
          }}
          placeholder={placeholder}
        />
      </div>
      {!valid && <p style={{ color: 'red', position: 'fixed' }}>Only incr of 1 allowed (1, 2, 3...)</p>}
    </>
  );
};

export default FormNumberInput;
