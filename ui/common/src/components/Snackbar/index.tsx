import React from 'react';
import { Snackbar as MuiSnackbar } from '@material-ui/core';
import MuiAlert from '@material-ui/lab/Alert';
import { SnackbarProps } from '../../types';

const Snackbar = ({ open, message, severity, duration = null, onClose, muiProps = {} }: SnackbarProps): JSX.Element => {
  if (!open) return null;

  return (
    <MuiSnackbar
      open={open}
      autoHideDuration={duration}
      onClose={onClose}
      id={`notification-${severity}`}
      {...muiProps}
    >
      <MuiAlert elevation={6} onClose={onClose} variant="filled" severity={severity || 'success'}>
        {message}
      </MuiAlert>
    </MuiSnackbar>
  );
};

export default Snackbar;
