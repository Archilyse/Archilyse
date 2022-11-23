import React from 'react';
import { C } from '../common';

const GoToCompetitionToolRenderer = ({ data }) => {
  const href = C.URLS.COMPETITION_TOOL(data.id);
  return (
    <a href={href} rel="noreferrer" target="_blank">
      Go to Competition Tool
    </a>
  );
};

export default GoToCompetitionToolRenderer;
