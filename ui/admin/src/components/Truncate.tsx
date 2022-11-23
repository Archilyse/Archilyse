import React, { useEffect, useState } from 'react';
import './truncate.scss';
import { Tooltip } from '@material-ui/core';

const Truncate = ({ maxWidth, children }) => {
  const [ref, setRef] = useState<HTMLSpanElement>();
  const [isOverflowed, setIsOverflowed] = useState(false);

  useEffect(() => {
    if (ref) {
      setIsOverflowed(ref.offsetWidth - maxWidth > 0);
    }
  }, [maxWidth, ref]);

  const truncatedText = (
    <span style={{ maxWidth }}>
      <div className="truncate-overflow" style={{ maxWidth }}>
        {children}
      </div>

      {/* create and hide element to compute a width without truncation */}
      <span ref={setRef} className="truncate-hidden">
        {children}
      </span>
    </span>
  );

  if (isOverflowed) {
    return (
      <Tooltip title={children} aria-label="add">
        {truncatedText}
      </Tooltip>
    );
  }

  return truncatedText;
};

export default Truncate;
