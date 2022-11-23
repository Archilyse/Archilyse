import React from 'react';
import { C } from '../common';

const StatusRenderer = row => {
  const fieldName = row.colDef.field;
  return (
    <div style={{ color: row.data[fieldName] === C.STATUS.SUCCESS ? 'green' : 'black' }} id="SimStatus">
      {row.data[fieldName]}
    </div>
  );
};

export default StatusRenderer;
