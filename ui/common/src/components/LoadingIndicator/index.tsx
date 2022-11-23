import React from 'react';
import cn from 'classnames';
import { CircularProgress, CircularProgressProps } from '@material-ui/core/';
import './loadingIndicator.scss';

type Props = { className?: string } & CircularProgressProps;

const LoadingIndicator = (props: Props): JSX.Element => (
  <div className={cn('loading-indicator', props.className)} role="alert" aria-busy="true">
    <CircularProgress {...props} />
  </div>
);

export default LoadingIndicator;
