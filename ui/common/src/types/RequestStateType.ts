export enum RequestStatus {
  IDLE,
  PENDING,
  FULFILLED,
  REJECTED,
  PARTIAL_FULFILLED,
}

export type RequestStateType<T = any> = {
  data: T | null;
  status: RequestStatus;
  error: null | string;
};
