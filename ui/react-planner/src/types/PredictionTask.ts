enum PredictionTaskStatus { // https://docs.celeryq.dev/en/stable/reference/celery.result.html#celery.result.AsyncResult.status
  PENDING = 'PENDING',
  STARTED = 'STARTED',
  RETRY = 'RETRY',
  FAILURE = 'FAILURE',
  SUCCESS = 'SUCCESS',
}

type PredictionTask = {
  id: string;
  status: PredictionTaskStatus;
};

export default PredictionTask;
