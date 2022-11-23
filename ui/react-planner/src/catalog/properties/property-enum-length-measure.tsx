import React from 'react';
import PropTypes from 'prop-types';
import { FormLabel, FormSelect } from '../../components/style/export';
import PropertyStyle from './shared-property-style';

export default function PropertyEnumLengthMeasure({ value, onUpdate, configs, sourceElement, internalState, state }) {
  const update = (value: number) => {
    const val = { value };
    if (configs.hook) {
      return configs.hook(val, sourceElement, internalState, state).then(_val => {
        return onUpdate(_val);
      });
    }

    return onUpdate(val);
  };

  return (
    <table className="PropertyEnumLengthMeasure" style={PropertyStyle.tableStyle}>
      <tbody>
        <tr>
          <td style={PropertyStyle.firstTdStyle}>
            <FormLabel htmlFor={configs.label}>{configs.label}</FormLabel>
          </td>
          <td>
            <FormSelect id={configs.label} value={value.value} onChange={event => update(Number(event.target.value))}>
              {(Object.entries(configs.values) as any).map(([label, value]) => (
                <option key={value.value} value={value.value}>
                  {label}
                </option>
              ))}
            </FormSelect>
          </td>
        </tr>
      </tbody>
    </table>
  );
}

PropertyEnumLengthMeasure.propTypes = {
  value: PropTypes.any.isRequired,
  onUpdate: PropTypes.func.isRequired,
  configs: PropTypes.object.isRequired,
  sourceElement: PropTypes.object,
  internalState: PropTypes.object,
  state: PropTypes.object.isRequired,
};
