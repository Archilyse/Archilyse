import { RequestHandler, rest } from 'msw';
import { setupServer } from 'msw/node';
import { ENDPOINTS } from '../../constants';

function buildHandler<T extends any>(
  pattern: RegExp | string,
  method: 'get' | 'put' | 'post' | 'delete',
  response: T,
  error?: number,
  delayResponse?: number
): RequestHandler {
  return rest[method](pattern, (req, res, ctx) => {
    if (error !== undefined) {
      return res(ctx.status(error), ctx.json(response));
    }
    if (delayResponse) ctx.delay(delayResponse);
    return res(ctx.json(response));
  });
}

const anyNumber = '\\d+';
const anyString = '\\w+';
const patterns = {
  ANNOTATION_PLAN: new RegExp(ENDPOINTS.ANNOTATION_PLAN(anyNumber, { validated: false })), // @TODO: Validate: true throws an error because the RegExp does not match
  ANNOTATION_PLAN_NOT_VALIDATED: new RegExp(ENDPOINTS.ANNOTATION_PLAN(anyNumber, { validated: false })),
  FLOORPLAN_IMG_PLAN: new RegExp(ENDPOINTS.FLOORPLAN_IMG_PLAN(anyNumber)),
  PLAN_BY_ID: new RegExp(ENDPOINTS.PLAN_BY_ID(anyNumber)),
  CLASSIFICATION_SCHEME: new RegExp(ENDPOINTS.CLASSIFICATION_SCHEME(anyString)),
  SITE_BY_ID: new RegExp(ENDPOINTS.SITE_BY_ID(anyNumber)),
  SITE_STRUCTURE: new RegExp(ENDPOINTS.SITE_STRUCTURE(anyNumber)),
  REQUEST_PREDICTION: new RegExp(ENDPOINTS.REQUEST_PREDICTION(anyNumber)),
  RETRIEVE_PREDICTION: new RegExp(ENDPOINTS.RETRIEVE_PREDICTION(anyNumber)),
};

const handlers = [
  buildHandler(patterns.ANNOTATION_PLAN, 'get', {}),
  buildHandler(patterns.ANNOTATION_PLAN_NOT_VALIDATED, 'put', {}),
  buildHandler(patterns.FLOORPLAN_IMG_PLAN, 'get', {}),
  buildHandler(patterns.PLAN_BY_ID, 'get', {}),
  buildHandler(patterns.CLASSIFICATION_SCHEME, 'get', {}),
  buildHandler(patterns.SITE_BY_ID, 'get', {}),
  buildHandler(patterns.SITE_STRUCTURE, 'get', {}),
];

const server = setupServer(...handlers);

export { server, buildHandler, patterns as ENDPOINTS_PATTERN };
