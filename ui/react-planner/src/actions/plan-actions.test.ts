import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import { FETCH_SITE_CLASSIFICATION_FULFILLED, FETCH_SITE_CLASSIFICATION_REJECTED } from '../constants';
import { MOCK_PLAN_RESPONSE, serverMocks } from '../tests/utils/';
import * as classificationResponse from '../tests/utils/mockGetClassification.json';
import * as actions from './plan-actions';

const { buildHandler, ENDPOINTS_PATTERN, server } = serverMocks;

const MOCK_SITE_RESPONSE = {
  created: '2021-03-17T12:01:04.005560',
  updated: '2021-03-17T12:05:48.818167',
  id: 321,
  classification_scheme: 'UNIFIED',
};

const MOCK_CLASSIFICATION_RESPONSE = classificationResponse;

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);

describe('Plan async actions', () => {
  let store;

  beforeAll(() => {
    server.listen();
  });

  beforeEach(() => {
    store = mockStore({});
  });

  afterEach(() => {
    server.resetHandlers();
  });

  afterAll(() => {
    server.close();
  });

  it('Fetches the available area types for the classification scheme via planId', async () => {
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.PLAN_BY_ID, 'get', MOCK_PLAN_RESPONSE, 200),
        buildHandler(ENDPOINTS_PATTERN.SITE_BY_ID, 'get', MOCK_SITE_RESPONSE, 200),
        buildHandler(ENDPOINTS_PATTERN.CLASSIFICATION_SCHEME, 'get', MOCK_CLASSIFICATION_RESPONSE, 200),
      ]
    );
    await store.dispatch(actions.fetchAvailableAreaTypes(MOCK_PLAN_RESPONSE));
    const lastAction = store.getActions().slice(-1)[0];
    expect(lastAction.type).toEqual(FETCH_SITE_CLASSIFICATION_FULFILLED);

    const fetchedPayload = lastAction.payload;
    expect(fetchedPayload).toStrictEqual(MOCK_CLASSIFICATION_RESPONSE);
  });

  it('Dispatches the same event if one of API calls failed', async () => {
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.PLAN_BY_ID, 'get', MOCK_PLAN_RESPONSE, 200),
        buildHandler(ENDPOINTS_PATTERN.SITE_BY_ID, 'get', { msg: 'No such site, gtfo' }, 404),
      ]
    );
    await store.dispatch(actions.fetchAvailableAreaTypes(MOCK_PLAN_RESPONSE));
    const lastAction = store.getActions().slice(-1)[0];
    expect(lastAction.type).toEqual(FETCH_SITE_CLASSIFICATION_REJECTED);
  });
});
