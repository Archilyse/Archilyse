import React from 'react';
import { Link } from 'react-router-dom';

const LinkRenderer = props => {
  const { id, href, target = '', text } = props;
  return (
    <Link key={id} to={href} target={target}>
      {text}
    </Link>
  );
};

export default LinkRenderer;
