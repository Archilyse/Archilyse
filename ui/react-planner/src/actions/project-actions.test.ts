import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import { GET_PROJECT_REJECTED, SAVE_PROJECT_PENDING, SAVE_PROJECT_REJECTED } from '../constants';
import { MOCK_ANNOTATIONS_RESPONSE, serverMocks } from '../tests/utils/';

import * as actions from './project-actions';

const { buildHandler, ENDPOINTS_PATTERN, server } = serverMocks;

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);

describe('Project async actions', () => {
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

  it('Fetches a non-existent project and dispatches an error action', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', { msg: 'msg: Entity not found payaso!' }, 404));
    const planId = MOCK_ANNOTATIONS_RESPONSE.plan_id;
    try {
      await store.dispatch(actions.getProjectAsync(planId, { onFulfill: () => {}, onReject: () => {} }));
    } catch (error) {
      const lastAction = store.getActions().slice(-1)[0];
      expect(lastAction.type).toEqual(GET_PROJECT_REJECTED);
    }
  });

  it(`Saves a project dispatching expected actions`, async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN_NOT_VALIDATED, 'put', MOCK_ANNOTATIONS_RESPONSE, 200));

    const EXPECTED_SAVE_ACTIONS = [SAVE_PROJECT_PENDING, SAVE_PROJECT_REJECTED]; // @TODO: Rejected because server mock has to be finetuned
    const planId = MOCK_ANNOTATIONS_RESPONSE.plan_id;

    await store.dispatch(
      actions.saveProjectAsync(
        { planId, state: jest.fn(), validated: false },
        { onFulfill: () => {}, onReject: () => {} }
      )
    );

    const dispatchedActions = store.getActions();
    dispatchedActions.forEach((action, index) => {
      const expectedAction = EXPECTED_SAVE_ACTIONS[index];
      expect(action.type).toBe(expectedAction);
    });
  });
});
