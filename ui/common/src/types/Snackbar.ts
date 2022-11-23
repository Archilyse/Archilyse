import { SnackbarProps as MuiSnackbarProps } from '@material-ui/core';
import { Color } from '@material-ui/lab/Alert';

export type SnackbarProps = {
  open: boolean;
  message: string | JSX.Element;
  severity: Color;
  duration?: number;
  muiProps?: MuiSnackbarProps;
  onClose: () => void;
};

export type SnackbarContextType = {
  data: Pick<SnackbarProps, 'message' | 'severity' | 'duration' | 'muiProps'>;
  show: (props: Pick<SnackbarProps, 'message' | 'severity' | 'duration' | 'muiProps'>) => void;
  close: () => void;
};
