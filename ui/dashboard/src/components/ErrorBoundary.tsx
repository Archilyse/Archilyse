import React from 'react';
import * as Sentry from '@sentry/browser';
import { SnackbarContext } from 'archilyse-ui-components';
import ProviderRequest from '../providers/request';
import { C } from '../common';
import { isChrome, isFirefox, isSafari } from '../common/modules';

const excludedErrorMsgs = [
  'NOISE simulation must be in SUCCESS state',
  'CONNECTIVITY simulation must be in SUCCESS state',
];
type ErrorState = {
  hasUIError: boolean;
};

const AUTH_ERRORS = [401, 403];
const SILENT_ERRORS = [404, 422];
const FOREVER = null; // `null` makes the snackbar persistent

const isServerError = error => [500, 502, 503, 504].includes(error?.response?.status);
const isBrowserSupported = () => isChrome() || isFirefox() || isSafari();

const getCustomErrorMessage = error => error?.response?.data?.msg;

const isExcludedError = error => excludedErrorMsgs.some(pattern => error.response?.data?.msg?.startsWith(pattern));

const hasErrorMessage = error => {
  const isSilentError = SILENT_ERRORS.includes(error.response?.status);
  if (isSilentError) return false;

  if (error.response.status === 500) {
    return true;
  }
  return Boolean(getCustomErrorMessage(error));
};

export const handleNetworkError = (error, context) => {
  if (isServerError(error)) {
    Sentry.captureException(error);
    context.show({ message: `Sorry, there was an error on the server: ${error.response.status}`, severity: 'error' });
    throw error;
  } else if (window.location.pathname === `/${C.SERVER_BASENAME}${C.URLS.LOGIN()}`) {
    throw error;
  } else if (error.response && AUTH_ERRORS.includes(error.response.status)) {
    window.location.pathname = `/${C.SERVER_BASENAME}${C.URLS.LOGIN()}`;
  } else {
    console.log('Error on network request', error);
    if (isExcludedError(error)) {
      return; // Do nothing
    }
    if (hasErrorMessage(error)) {
      const customMsg = getCustomErrorMessage(error);
      if (customMsg) context.show({ message: `${getCustomErrorMessage(error)}`, severity: 'error' });
    }
    throw error;
  }
};
class ErrorBoundary extends React.Component<{}, ErrorState> {
  constructor(props) {
    super(props);
    this.state = { hasUIError: false };
  }

  handleNetworkError = error => handleNetworkError(error, this.context);

  componentDidMount() {
    ProviderRequest.instance.interceptors.response.use(
      res => res,
      error => this.handleNetworkError(error)
    );
    if (!isBrowserSupported()) {
      const message =
        'Your browser is not supported. For a better user experience, please download the latest version of Chrome, Firefox or Safari.';
      this.context.show({ message, severity: 'info', duration: FOREVER });
    }
  }

  componentDidCatch(error, info) {
    console.log('Global error while rendering component', error);
    console.log('Stack info', info);

    Sentry.withScope(scope => {
      scope.setExtras(info);
      Sentry.captureException(error);
    });

    this.setState({ hasUIError: true });
  }

  render() {
    const { hasUIError } = this.state;
    if (hasUIError) {
      return <h2>Something went wrong, please contact technical support.</h2>;
    }

    return this.props.children;
  }
}

ErrorBoundary.contextType = SnackbarContext;

export default ErrorBoundary;
