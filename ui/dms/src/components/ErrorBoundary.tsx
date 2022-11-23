import React from 'react';
import * as Sentry from '@sentry/browser';
import { SnackbarContext } from 'archilyse-ui-components';
import ProviderRequest from '../providers/request';
import { C } from '../common';

// @TODO: Move this component to common and re-use it in other apps, is virtually identical in all of them but in Admin UI

type ErrorState = {
  hasUIError: boolean;
};

const AUTH_ERRORS = [401, 403];
const SILENT_ERRORS = [404]; // We don't want to show a snackbar for this
const FOREVER = null; // `null` makes the snackbar persistent

const ENDPOINTS_WITH_HANDLED_ERRORS = [C.ENDPOINTS.FILE()];

const currentWindow: any = window;

const BASE_LOGIN_URL = `${C.URLS.BASE_PATH}${C.URLS.LOGIN()}`;

const isChrome = () => !!currentWindow.chrome && (!!currentWindow.chrome.webstore || !!currentWindow.chrome.runtime);
const isFirefox = () => typeof currentWindow.InstallTrigger !== 'undefined';
const isSafari = () => navigator.userAgent.indexOf('Safari') !== -1;

const isServerError = error => [500, 502, 503, 504].includes(error?.response?.status);
const isBrowserSupported = () => isChrome() || isFirefox() || isSafari();

const hasCustomErrorMessage = error => error.response && error.response.data && error.response.data.msg;

const errorIsHandled = error => {
  if (!error.response.config) return false;
  const { config } = error.response;
  return ENDPOINTS_WITH_HANDLED_ERRORS.includes(config.url) && config.method === 'post';
};

// @TODO: Instead of this, use an interceptor or custom param in the request to know if we have to display an error or not
const displayGenericErrorMessage = error => {
  if (!error.response) return true;
  if (errorIsHandled(error)) return false;
  const isSilentError = SILENT_ERRORS.includes(error.response?.status);
  const genericServerError = error.response.status === 500;
  if (genericServerError) {
    return true;
  }
  return !isSilentError && !hasCustomErrorMessage(error);
};

export const handleNetworkError = (error, context) => {
  if (isServerError(error)) {
    Sentry.captureException(error);
    context.show({ message: `Sorry, there was an error on the server: ${error.response.status}`, severity: 'error' });
    throw error;
  } else if (window.location.pathname === BASE_LOGIN_URL) {
    throw error;
  } else if (error.response && AUTH_ERRORS.includes(error.response.status)) {
    window.location.pathname = BASE_LOGIN_URL;
  } else {
    if (displayGenericErrorMessage(error)) {
      context.show({ message: `${error}`, severity: 'error' });
    }
    throw error;
  }
};
class ErrorBoundary extends React.Component<any, ErrorState> {
  constructor(props) {
    super(props);
    this.state = {
      hasUIError: false,
    };
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
