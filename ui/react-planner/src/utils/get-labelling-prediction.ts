import { ProviderRequest } from '../providers';
import { ENDPOINTS, OPENING_TYPE } from '../constants';
import { Prediction, RequestPredictionResponse, RetrievePredictionResponse } from '../types';

// Below constants will make the app poll during 300 sec before giving up
const MAX_POLL_ITERATIONS = 30;
const POLL_INTERVAL_MS = 10 * 1000;

export const POLLING_TIMEOUT_ERROR = 'Timeout while waiting for the prediction';
export const CLEARING_TIMER_MESSAGE = 'Clearing poll timer';

const resultsAreReady = response => response?.type === 'FeatureCollection'; // @TODO: Or simply response is different than undefined  return true

/* eslint-disable */
let timer = null;
/* eslint-enable */

const { DOOR, WINDOW } = OPENING_TYPE;

const isAHole = feature => [DOOR, WINDOW].includes(feature.properties.label.toLowerCase());
const isAnItem = feature => !isAHole(feature);

const cancelPolling = timer => {
  console.debug(CLEARING_TIMER_MESSAGE);
  clearInterval(timer);
  timer = null;
};

const pollData = async (url): Promise<RetrievePredictionResponse> => {
  let response = null;
  let iterations = 0;

  return new Promise((resolve, reject) => {
    const t = setInterval(async () => {
      try {
        if (iterations > MAX_POLL_ITERATIONS) {
          cancelPolling(timer);

          console.error(`Max poll iterations reached, API did not respond with results`);
          return reject(POLLING_TIMEOUT_ERROR);
        }

        response = await ProviderRequest.get(url);
        if (resultsAreReady(response)) {
          cancelPolling(timer);
          return resolve(response);
        } else {
          console.debug(`Still processing ...`);
        }

        iterations++;
      } catch (error) {
        cancelPolling(timer);
        return reject(error);
      }
    }, POLL_INTERVAL_MS);
    timer = t;
  });
};

const requestPrediction = async (planId: string): Promise<RequestPredictionResponse> => {
  const response: RequestPredictionResponse = await ProviderRequest.get(ENDPOINTS.REQUEST_PREDICTION(planId));
  return response;
};

const fetchResults = async (tasks: RequestPredictionResponse): Promise<RetrievePredictionResponse> => {
  const { icon_task } = tasks;
  return pollData(ENDPOINTS.RETRIEVE_PREDICTION(icon_task.id));
};

const parseResults = (results: RetrievePredictionResponse): Prediction => {
  return {
    lines: [], // @TODO Add it once we have line rendering logic more refined
    holes: results.features.filter(feature => isAHole(feature)),
    items: results.features.filter(feature => isAnItem(feature)),
  };
};

const getLabellingPrediction = async (planId: string): Promise<Prediction> => {
  cancelPolling(timer);

  const tasks = await requestPrediction(planId);
  const result = await fetchResults(tasks);
  const prediction = parseResults(result);
  return prediction;
};

export default getLabellingPrediction;
