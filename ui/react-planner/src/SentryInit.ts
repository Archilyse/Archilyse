import * as Sentry from '@sentry/browser';
import { CaptureConsole } from '@sentry/integrations';
import { BrowserTracing } from '@sentry/tracing';

export const SentryInit = ({ isProduction, store }) => {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    enabled: isProduction,
    environment: 'editor-v2-ui',
    tracesSampleRate: 0.1,
    integrations: [
      new BrowserTracing(),
      new CaptureConsole({
        levels: ['error'],
      }) as CaptureConsole,
    ],
  });

  Sentry.addGlobalEventProcessor(event => {
    try {
      const reduxState = store.getState();
      const client = Sentry.getCurrentHub().getClient();
      const endpoint = attachmentUrlFromDsn(client.getDsn(), event.event_id);
      const formData = new FormData();
      formData.append(
        'redux-state',
        new Blob([JSON.stringify(reduxState)], {
          type: 'application/json',
        }),
        'redux-state.json'
      );
      fetch(endpoint, {
        method: 'POST',
        body: formData,
      }).catch(ex => {
        // we have to catch this otherwise it throws an infinite loop in Sentry
        console.error(ex);
      });
      return event;
    } catch (ex) {
      console.error(ex);
    }
  });
};

function attachmentUrlFromDsn(dsn, eventId: string) {
  const { host, path, projectId, port, protocol, user } = dsn;
  return `${protocol}://${host}${port !== '' ? `:${port}` : ''}${
    path !== '' ? `/${path}` : ''
  }/api/${projectId}/events/${eventId}/attachments/?sentry_key=${user}&sentry_version=7&sentry_client=custom-javascript`;
}
