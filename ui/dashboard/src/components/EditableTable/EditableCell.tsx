import React, { useState } from 'react';
import { Tooltip } from '@material-ui/core';
import { Editable, EditableProps, Icon } from 'archilyse-ui-components';
import './editableCell.scss';

export interface EditableCellProps extends EditableProps {
  onRemove?: () => void;
  component?: 'th' | 'td';
  placeholder?: string;
  renderTitle?: (value: string | number) => React.ReactNode;
}

const EditableCell = ({
  component: TableCell = 'td',
  value,
  onRemove,
  onSave,
  placeholder,
  renderTitle,
  ...editableProps
}: EditableCellProps): JSX.Element => {
  const [editing, setEditing] = useState(false);

  const handleDoubleClick = () => {
    setEditing(true);
  };

  const handleSave = value => {
    onSave(value);
    setEditing(false);
  };

  const _renderTitle = () => {
    if (value !== undefined && value !== null) {
      if (renderTitle) return renderTitle(value);

      return value;
    }

    if (placeholder) return <span className="placeholder">{placeholder}</span>;

    return null;
  };

  return (
    <TableCell className="editable-cell" onDoubleClick={handleDoubleClick}>
      <Editable
        value={value || ''}
        editing={editing}
        onCancel={() => setEditing(false)}
        onSave={handleSave}
        {...editableProps}
        inputProps={{ className: 'editable-cell-input', name: 'editable-cell', ...(editableProps.inputProps || {}) }}
      >
        <span className="editable-cell-value">{_renderTitle()}</span>
        {onRemove && (
          <Tooltip title="Remove">
            <button className="editable-cell-remove" onClick={onRemove}>
              <Icon style={{ fontSize: 25 }}>remove_circle_outline_rounded</Icon>
            </button>
          </Tooltip>
        )}
      </Editable>
    </TableCell>
  );
};

export default EditableCell;
