import React, { useState } from 'react';
import { Chip } from '@material-ui/core';
import './tag.scss';

const Tag = ({ label, chipProps }) => {
  const [showCross, setShowCross] = useState(false);
  return (
    <div>
      <Chip
        {...chipProps}
        className="custom-tag"
        onMouseEnter={() => setShowCross(true)}
        onMouseLeave={() => setShowCross(false)}
        style={{ color: '#434c50', backgroundColor: '#ECEDED' }}
        label={label}
        onDelete={showCross ? chipProps.onDelete : null}
      />
    </div>
  );
};

export default Tag;
