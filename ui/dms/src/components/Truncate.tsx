import React, { useEffect, useState } from 'react';
import './truncate.scss';
import { Tooltip } from '@material-ui/core';

type Props = {
  maxWidth: number;
  maxHeight?: number;
  type?: 'overflow' | 'middle';
};

const truncateInMiddle = (maxWidth: number, refWidth: number, text: string) => {
  const letterWidth = refWidth / text.length;
  const availableLetters = maxWidth / letterWidth;

  return text.slice(0, availableLetters / 2) + '..' + text.slice(text.length - availableLetters / 2, text.length);
};

const Truncate = ({
  maxWidth,
  maxHeight,
  children,
  type = 'overflow',
}: React.PropsWithChildren<Props>): JSX.Element => {
  const [widthRef, setWidthRef] = useState<HTMLSpanElement>();
  const [heightRef, setHeightRef] = useState<HTMLSpanElement>();
  const [isOverflowed, setIsOverflowed] = useState(false);

  useEffect(() => {
    if (widthRef && heightRef) {
      setIsOverflowed(widthRef.offsetWidth > maxWidth || heightRef.offsetHeight > maxHeight);
    }
  }, [maxWidth, widthRef, heightRef]);

  const className = type === 'overflow' ? 'truncate-overflow' : '';

  const getTruncatedComponent = text => (
    <span style={{ maxWidth }}>
      <div className={className} style={{ maxWidth }}>
        {text}
      </div>

      {/* create and hide element to compute a width without truncation */}
      <span ref={setWidthRef} aria-hidden={true} className="truncate-hidden">
        {children}
      </span>
      <span ref={setHeightRef} aria-hidden={true} className="truncate-hidden" style={{ maxWidth }}>
        {children}
      </span>
    </span>
  );

  if (isOverflowed) {
    const truncatedText =
      type === 'overflow' ? children : truncateInMiddle(maxWidth, widthRef.offsetWidth, children as string);
    return (
      <Tooltip title={children} aria-label="add">
        {getTruncatedComponent(truncatedText)}
      </Tooltip>
    );
  }

  return getTruncatedComponent(children);
};

export default Truncate;
