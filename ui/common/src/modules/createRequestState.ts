import { RequestStateType, RequestStatus } from '../types';

export default function createRequestState<T extends any>(data: T = null): RequestStateType<T> {
  return {
    data,
    status: RequestStatus.IDLE,
    error: null,
  };
}
