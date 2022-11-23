import React from 'react';

type AddSvgProps = {
  style?: React.CSSProperties;
};

const AddSvg = ({ style = {} }: AddSvgProps): JSX.Element => (
  <svg style={{ width: 30, height: 30, ...style }} viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
    <line x1="6" y1="2.5" x2="4" y2="6.5" stroke="#C3C6C7" strokeWidth="0.6" />
  </svg>
);
export default AddSvg;
