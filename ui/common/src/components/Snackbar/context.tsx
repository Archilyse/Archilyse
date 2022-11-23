import React, { useState } from 'react';
import { SnackbarContextType } from '../../types';
import Snackbar from '.';

const initalSnackbarState: SnackbarContextType = {
  data: { message: null, severity: 'success', duration: 3000, muiProps: {} },
  show: () => null,
  close: () => null,
};

const SnackbarContext = React.createContext(initalSnackbarState);

export const SnackbarContextProvider = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [snackbar, setSnackbar] = useState(initalSnackbarState.data);

  const handleClose = () => {
    setSnackbar(initalSnackbarState.data);
    setOpen(false);
  };

  const handleOpen = (data: SnackbarContextType['data']) => {
    setSnackbar({ ...data });
    setOpen(true);
  };

  return (
    <SnackbarContext.Provider value={{ data: snackbar, show: handleOpen, close: handleClose }}>
      {children}

      <Snackbar open={open} {...snackbar} onClose={handleClose} />
    </SnackbarContext.Provider>
  );
};

export default SnackbarContext;
