import { Paper } from '@material-ui/core';
import React from 'react';
import './paperCard.scss';

const PaperCard = ({ title, children }) => {
  return (
    <div className="paper-card-container">
      <h3>{title}</h3>
      <Paper elevation={0}>{children}</Paper>
    </div>
  );
};

export default PaperCard;
