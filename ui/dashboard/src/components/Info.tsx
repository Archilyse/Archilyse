import React from 'react';
import { Tooltip } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import './info.scss';

const customStyles = makeStyles(theme => ({
  tooltip: {
    fontSize: '14px',
  },
}));

type Props = {
  text: string;
  width?: string | number;
  height?: string | number;
};

const Info = ({ text, width = 20, height = 20 }: Props): JSX.Element => {
  const classes = customStyles();
  return (
    <Tooltip classes={classes} title={text}>
      <small className="info-tooltip" style={{ width, height }} role="img" aria-label="info">
        i
      </small>
    </Tooltip>
  );
};

export default Info;
