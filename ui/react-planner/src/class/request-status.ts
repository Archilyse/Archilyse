import { RequestStatusType } from '../constants';
import { State } from '../models';

type Status = {
  status: string;
  error: string;
};

class RequestStatus {
  static setPending(state: State, actionName: string): State {
    const status = { status: RequestStatusType.PENDING, error: null };

    return RequestStatus._updateState(state, actionName, status);
  }

  static setFulfilled(state: State, actionName: string): State {
    const status = { status: RequestStatusType.FULFILLED, error: null };

    return RequestStatus._updateState(state, actionName, status);
  }

  static setRejected(state: State, actionName: string, error?: string): State {
    const status = { status: RequestStatusType.REJECTED, error: error || 'Error occurred' };

    return RequestStatus._updateState(state, actionName, status);
  }

  static _updateState(state: State, actionName: string, status: Status): State {
    state.requestStatus[actionName] = status;
    return state;
    // return state.updateIn(['requestStatus'], requestStatus => requestStatus.set(actionName, status));
  }
}

export default RequestStatus;
