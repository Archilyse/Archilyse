import React, { useState } from 'react';
import { Editable, EditableProps, Icon, INPUT_TYPES } from 'archilyse-ui-components';
import './inputWithIcon.scss';

interface Props extends EditableProps {
  text?: string;
  iconSize: number;
}

const InputWithIcon = ({ text, value, onSave, inputProps, iconSize, ...editableProps }: Props): JSX.Element => {
  const [editing, setEditing] = useState(false);

  const handleWeightChange = (value: string | number) => {
    setEditing(false);

    onSave(value);
  };
  return (
    <div className="input-with-icon">
      <Editable
        editing={editing}
        value={value}
        onSave={handleWeightChange}
        onCancel={() => setEditing(false)}
        type={INPUT_TYPES.number}
        inputProps={{
          className: 'weight-input',
          step: 0.1,
          min: 0,
          ...inputProps,
        }}
        {...editableProps}
      >
        <span onDoubleClick={() => setEditing(true)} className="editable">
          {text || value}
        </span>
      </Editable>
      <button onClick={() => setEditing(!editing)}>
        <Icon style={{ fontSize: iconSize }}>edit</Icon>
      </button>
    </div>
  );
};

export default InputWithIcon;
