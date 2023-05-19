import { serverMocks } from '../tests/utils/';
import { PredictionTask, RequestPredictionResponse, RetrievePredictionResponse } from '../types';
import getLabellingPrediction, { CLEARING_TIMER_MESSAGE, POLLING_TIMEOUT_ERROR } from './get-labelling-prediction';

const { buildHandler, ENDPOINTS_PATTERN, server } = serverMocks;

const originalSetInterval = global.setInterval;
const MOCK_PLAN_ID = '1';
const MOCK_REQUEST_PREDICTION_RESPONSE: RequestPredictionResponse = {
  icon_task: {
    status: 'PENDING' as PredictionTask['status'],
    id: '12',
  },
};
const MOCK_RETRIEVE_PREDICTION_RESPONSE: RetrievePredictionResponse = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [[[], [], [], [], []]] },
      properties: { label: 'DOOR' },
    },
    {
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [[[], [], [], [], []]] },
      properties: { label: 'WINDOW' },
    },
    {
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [[[], [], [], [], []]] },
      properties: { label: 'BATHROOM' },
    },
  ],
};

const mockSuccesfullPredictionResponse = () => {
  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.REQUEST_PREDICTION, 'get', MOCK_REQUEST_PREDICTION_RESPONSE, 200),
      buildHandler(ENDPOINTS_PATTERN.RETRIEVE_PREDICTION, 'get', MOCK_RETRIEVE_PREDICTION_RESPONSE, 200),
    ]
  );
};

const mockTimeoutPredictionResponse = () => {
  const MOCK_PENDING_RESPONSE = {}; // Will force to always keep polling
  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.REQUEST_PREDICTION, 'get', MOCK_REQUEST_PREDICTION_RESPONSE, 200),
      buildHandler(ENDPOINTS_PATTERN.RETRIEVE_PREDICTION, 'get', MOCK_PENDING_RESPONSE, 200),
    ]
  );
};
describe('getLabellingPrediction', () => {
  beforeAll(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
    jest.clearAllMocks();
  });

  afterAll(() => {
    jest.useRealTimers();
    server.close();
  });

  it('Successfully retrieves a prediction after polling', async () => {
    const EXPECTED_PREDICTED_LINES = 0;
    const EXPECTED_PREDICTED_ITEMS = 1;
    const EXPECTED_PREDICTED_HOLES = 2;

    const pollTimer = jest.spyOn(global, 'setInterval').mockImplementation((fn: Function) => fn());
    mockSuccesfullPredictionResponse();

    const prediction = await getLabellingPrediction(MOCK_PLAN_ID);
    expect(pollTimer).toBeCalled();

    expect(prediction.lines).toHaveLength(EXPECTED_PREDICTED_LINES);
    expect(prediction.items).toHaveLength(EXPECTED_PREDICTED_ITEMS);
    expect(prediction.holes).toHaveLength(EXPECTED_PREDICTED_HOLES);
  });

  it('If prediction times out, an error is shown and no more requests are made', async () => {
    //Mock setInterval to make it execute way faster than the original so we time out (NOTE that using fake timers won't work because the iterations variable are not correctly tracked)
    jest.spyOn(global, 'setInterval').mockImplementation((fn: Function): any => {
      originalSetInterval(() => fn(), 10);
    });
    const consoleDebug = jest.spyOn(console, 'debug');

    mockTimeoutPredictionResponse();
    try {
      await getLabellingPrediction(MOCK_PLAN_ID);
    } catch (error) {
      expect(error).toBe(POLLING_TIMEOUT_ERROR);
      expect(consoleDebug).toHaveBeenLastCalledWith(CLEARING_TIMER_MESSAGE);
    }
  });
});
