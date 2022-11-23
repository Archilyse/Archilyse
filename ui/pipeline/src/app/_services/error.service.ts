import { ErrorHandler, Injectable } from '@angular/core';
import * as Sentry from '@sentry/browser';
import { environment } from 'src/environments/environment';

interface Error {
  originalStack: any;
  zoneAwareStack: any;
  stack: any;
  rejection: any;
  promise: any;
  zone: any;
  task: any;
}

const ACCEPTED_HTTP_ERROR_CODES = [400, 404, 422];

// Only in production
const sentryActivated = window.location.href.startsWith('https://');
if (sentryActivated) {
  Sentry.init({
    dsn: environment.sentryDSN,
    environment: 'pipeline-ui',
  });
} else {
  // tslint:disable-next-line:no-console
  console.info('SENTRY DISABLED');
}

const isHTTPError = error => ACCEPTED_HTTP_ERROR_CODES.includes(error.rejection?.status);
@Injectable()
export class SentryErrorHandler implements ErrorHandler {
  constructor() {}
  handleError(error: Error) {
    if (isHTTPError(error)) {
      console.error(`Handled HTTP error ${error}`);
      return;
    }
    if (sentryActivated) {
      Sentry.captureException(error);
    }
    throw error;
  }
}
