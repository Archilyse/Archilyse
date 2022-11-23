import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import { fulfilledClassification, rejectedClassification } from '../actions/plan-actions';
import * as classificationResponse from '../tests/utils/mockGetClassification.json';
import plans from './plan-reducer';

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);

describe('Plan reducers', () => {
  beforeEach(() => {
    mockStore({});
  });

  it('Returns the initial state when the event is not applicable', () => {
    const state = { just: 'passing by' };
    const action = { type: 'not applicable' };
    expect(plans(state, action)).toEqual(state);
  });

  it('Returns the initial state when there was a failure to get area types', () => {
    const state = { just: 'passing by' };
    const action = rejectedClassification('big focking error');
    expect(plans(state, action)).toEqual(state);
  });

  it('Calls "Plan.setAvailableAreaTypes" on applicable event', () => {
    const action = fulfilledClassification(classificationResponse);
    const state = {};
    const reducerResult = plans(state, action);
    const hasAvailableAreaTypes = reducerResult.hasOwnProperty('availableAreaTypes');
    expect(hasAvailableAreaTypes).toEqual(true);
  });
});
