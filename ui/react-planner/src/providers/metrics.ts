// This provider assumes we are using Simple Analytics and its custom events feature: https://docs.simpleanalytics.com/events
import { METRICS_EVENTS, PREDICTION_FEEDBACK_EVENTS } from '../constants';

type metadata = {
  plan_id: number;
  group_id: number;
};

const emptyFn = () => {};

class ProviderMetrics {
  timers: Record<METRICS_EVENTS, number> | {};
  metadata: metadata;
  sendEvent: (
    eventName: METRICS_EVENTS | PREDICTION_FEEDBACK_EVENTS,
    metadata: metadata & { duration_seconds?: number }
  ) => void;
  trackPage: (path: string, metadata: metadata) => void;

  constructor() {
    this.timers = {};

    this.sendEvent = window.sa_event || emptyFn;
    this.trackPage = window.sa_pageview || emptyFn;
  }

  initMetadata(metadata: metadata) {
    this.metadata = metadata;
  }

  trackPageView() {
    this.trackPage(window.location.pathname, this.metadata);
  }

  startTrackingEvent(eventName: METRICS_EVENTS) {
    if (!this.timers[eventName]) {
      this.timers[eventName] = performance.now();
    }
  }

  endTrackingEvent(eventName: METRICS_EVENTS) {
    const duration_seconds = (performance.now() - this.timers[eventName]) / 1000;
    this.sendEvent(eventName, { ...this.metadata, duration_seconds: parseFloat(duration_seconds.toFixed(2)) });
    delete this.timers[eventName];
  }

  trackPredictionFeedback(eventName: PREDICTION_FEEDBACK_EVENTS) {
    this.sendEvent(eventName, { ...this.metadata });
  }

  clearTrackedEvents() {
    this.timers = {};
  }
}

export default new ProviderMetrics();
