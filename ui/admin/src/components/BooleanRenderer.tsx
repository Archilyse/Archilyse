import React from 'react';
import { Icon } from 'archilyse-ui-components';

const BooleanRenderer = row => {
  const fieldName = row.colDef.field;
  if (row.data[fieldName]) {
    return (
      <div style={{ color: 'green' }} className="check">
        <Icon style={{ color: 'inherit', marginLeft: undefined }}>check</Icon>
      </div>
    );
  } else {
    return (
      <div style={{ color: 'red' }} className="cross">
        <Icon style={{ color: 'inherit', marginLeft: undefined }}>close</Icon>
      </div>
    );
  }
};

export default BooleanRenderer;
