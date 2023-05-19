import PredictionTask from './PredictionTask';

type RequestPredictionResponse = {
  wall_task?: PredictionTask;
  icon_task: PredictionTask;
};

export default RequestPredictionResponse;
