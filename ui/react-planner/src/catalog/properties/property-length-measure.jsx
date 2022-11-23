import React from 'react';
import convert from 'convert-units';
import { MdKeyboardArrowDown, MdKeyboardArrowUp } from 'react-icons/md';
import { FormLabel, FormTextInput } from '../../components/style/export';
import { MEASURE_STEP_FALLBACK, UNIT_CENTIMETER } from '../../constants';
import { toFixedFloat } from '../../utils/math';
import PropertyStyle from './shared-property-style';

const internalTableStyle = { borderCollapse: 'collapse' };
const secondTdStyle = { padding: 0 };

export default function PropertyLengthMeasure({
  value,
  onUpdate,
  onValid,
  configs,
  sourceElement,
  internalState,
  state,
  propertyName,
}) {
  const unit = UNIT_CENTIMETER;
  const { hook, label, step, defaultValue, ...configRest } = configs;
  const length = value.value || defaultValue;

  const MEASURE_STEP = step || MEASURE_STEP_FALLBACK;

  const update = (lengthInput, unitInput) => {
    const newLength = toFixedFloat(lengthInput);
    const merged = {
      ...value,
      value: unitInput !== UNIT_CENTIMETER ? convert(newLength).from(unitInput).to(UNIT_CENTIMETER) : newLength,
    };

    if (hook) {
      return hook(merged, sourceElement, internalState, state).then(val => {
        return onUpdate(val);
      });
    }

    return onUpdate(merged);
  };
  const onClickUp = () => {
    update(length + MEASURE_STEP, unit);
  };

  const onClickDown = () => {
    update(length - MEASURE_STEP, unit);
  };

  return (
    <table className="PropertyLengthMeasure" style={{ ...PropertyStyle.tableStyle, height: '80px' }}>
      <tbody>
        <tr>
          <td style={PropertyStyle.firstTdStyle}>
            <FormLabel>{label}</FormLabel>
          </td>
          <td style={secondTdStyle}>
            <table style={internalTableStyle}>
              <tbody>
                <tr>
                  <td>
                    <FormTextInput
                      id={`${propertyName}-value-display`}
                      data-testid={`${propertyName}-value-display`}
                      style={{ backgroundColor: 'lightgray', width: '70px' }}
                      value={`${length} ${unit}`}
                      disabled={true}
                      propertyname={propertyName}
                      {...configRest}
                    />
                  </td>
                  <td style={{ display: 'flex', flexDirection: 'column', marginLeft: '2px' }}>
                    <button id={`incr-${propertyName}`} style={{ width: '30px' }} onClick={onClickUp}>
                      <MdKeyboardArrowUp />
                    </button>
                    <button id={`decr-${propertyName}`} style={{ width: '30px' }} onClick={onClickDown}>
                      <MdKeyboardArrowDown />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
