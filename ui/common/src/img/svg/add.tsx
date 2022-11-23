import React from 'react';

type AddSvgProps = {
  style?: React.CSSProperties;
};

const AddSvg = ({ style = {} }: AddSvgProps): JSX.Element => (
  <svg style={{ width: 56, height: 56, ...style }} viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <line x1="19" y1="27.5" x2="37" y2="27.5" stroke="#898989" />
    <line x1="28.5" y1="19" x2="28.5" y2="37" stroke="#898989" />
    <circle cx="28" cy="28" r="27.5" stroke="#898989" />
  </svg>
);
export default AddSvg;
