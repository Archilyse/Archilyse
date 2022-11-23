import React from 'react';
import ReactDOM from 'react-dom';
import * as Sentry from '@sentry/browser';
import App from './App';

const PRODUCTION = 'production';

const isProduction = window.location.protocol === 'https:' && process.env.NODE_ENV === PRODUCTION;
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  enabled: isProduction,
  environment: 'dms-ui',
});

ReactDOM.render(<App />, document.getElementById('root'));
