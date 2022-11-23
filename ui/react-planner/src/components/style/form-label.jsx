import React from 'react';

const BASE_STYLE = {
  display: 'block',
  marginBottom: '5px',
};

export default function FormLabel({ children, style, formName = '', ...rest }) {
  return (
    <label htmlFor={formName} style={{ ...BASE_STYLE, style }} {...rest}>
      {children}
    </label>
  );
}
