import React from 'react';
import { Tooltip } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';

const customStyles = makeStyles(theme => ({
  tooltip: {
    fontSize: '14px',
  },
}));

type Props = {
  title: string;
  children: React.ReactElement;
};

const CompetitionTooltip = ({ title, children }: Props): JSX.Element => {
  const classes = customStyles();
  return (
    <Tooltip classes={classes} title={title}>
      {children}
    </Tooltip>
  );
};

export default CompetitionTooltip;
