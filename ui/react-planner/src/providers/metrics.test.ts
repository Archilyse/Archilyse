import { METRICS_EVENTS } from '../constants';
import ProviderMetrics from './metrics';

const WAIT_SECONDS = 0.5;
const sleep = async (seconds): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, seconds * 1000));
};

describe('ProviderMetrics', () => {
  afterEach(() => {
    ProviderMetrics.clearTrackedEvents();
    ProviderMetrics.initMetadata({ plan_id: undefined, group_id: undefined });
    jest.restoreAllMocks();
  });

  describe('initMetadata', () => {
    const MOCK_METADATA = { group_id: 777, plan_id: 1 };

    it('sets metadata properly', () => {
      expect(ProviderMetrics.metadata).toBe(undefined);

      ProviderMetrics.initMetadata(MOCK_METADATA);

      expect(ProviderMetrics.metadata).toStrictEqual(MOCK_METADATA);
    });

    it('sends metadata with tracking method once is set', async () => {
      const sendEventMock = jest.spyOn(ProviderMetrics, 'sendEvent').mockImplementation(() => jest.fn());
      const trackPageMock = jest.spyOn(ProviderMetrics, 'trackPage').mockImplementation(() => jest.fn());

      // Set metadata
      ProviderMetrics.initMetadata(MOCK_METADATA);

      // Expect it on tracking a page view
      ProviderMetrics.trackPageView();
      expect(trackPageMock).toBeCalledWith('/', MOCK_METADATA);

      // And in an event
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      await sleep(WAIT_SECONDS);
      ProviderMetrics.endTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      expect(sendEventMock).toBeCalledWith(METRICS_EVENTS.DRAWING_ITEM, {
        ...MOCK_METADATA,
        duration_seconds: WAIT_SECONDS,
      });
    });
  });

  describe('trackPageView', () => {
    const MOCK_PATHNAME = '/labelling_at_its_fullest';
    const originalLocation = window.location;

    beforeEach(() => {
      delete global.window.location;
      global.window.location = Object.assign({}, originalLocation);
      window.location.pathname = MOCK_PATHNAME;
    });

    afterEach(() => {
      window.location = location;
    });

    it('tracks the current page on the metrics service', () => {
      const trackPageMock = jest.spyOn(ProviderMetrics, 'trackPage').mockImplementation(() => jest.fn());

      ProviderMetrics.trackPageView();
      expect(trackPageMock).toBeCalledWith(MOCK_PATHNAME, { group_id: undefined, plan_id: undefined });
    });
  });

  describe('startTrackingEvent', () => {
    it('starts a timer with an event name', () => {
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      expect(ProviderMetrics.timers[METRICS_EVENTS.DRAWING_ITEM]).toBeTruthy();
    });

    it('does not restart and already started timer', async () => {
      // Start the timer
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      const initialValue = ProviderMetrics.timers[METRICS_EVENTS.DRAWING_ITEM];

      await sleep(WAIT_SECONDS);

      // If we start it again after half a second, value remains the initial one
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      expect(ProviderMetrics.timers[METRICS_EVENTS.DRAWING_ITEM]).toBe(initialValue);
    });
  });

  describe('endTrackingEvent', () => {
    it('ends a timer with an event name and send the custom event to the metrics service', async () => {
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      const sendEventMock = jest.spyOn(ProviderMetrics, 'sendEvent').mockImplementation(() => jest.fn());

      await sleep(WAIT_SECONDS);

      ProviderMetrics.endTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);

      expect(sendEventMock).toBeCalledWith(METRICS_EVENTS.DRAWING_ITEM, { duration_seconds: WAIT_SECONDS });
      expect(ProviderMetrics.timers[METRICS_EVENTS.DRAWING_ITEM]).toBeUndefined();
    });
  });

  describe('clearTrackedEvents', () => {
    it('clear all timers', () => {
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_ITEM);
      expect(ProviderMetrics.timers[METRICS_EVENTS.DRAWING_ITEM]).toBeTruthy();

      ProviderMetrics.clearTrackedEvents();
      expect(ProviderMetrics.timers).toStrictEqual({});
    });
  });
});
