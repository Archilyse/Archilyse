import { RequestHandler, rest } from 'msw';
import { setupServer } from 'msw/node';
import C from 'Common/constants';
import { PotentialSimulationInfo } from 'Common/types';

function buildHandler<T extends any>(
  pattern: RegExp | string,
  method: 'get' | 'put' | 'post' | 'delete',
  response: T,
  error?: number
): RequestHandler {
  return rest[method](pattern, (req, res, ctx) => {
    if (error !== undefined) {
      return res(ctx.status(error), ctx.json(response));
    }

    return res(ctx.json(response));
  });
}

const anyNumber = '\\d+';

const patterns = {
  SIMULATION: new RegExp(C.ENDPOINTS.SIMULATION(anyNumber)),
};

const handlers = [buildHandler<PotentialSimulationInfo>(patterns.SIMULATION, 'get', null)];

const server = setupServer(...handlers);

export { server, buildHandler, patterns as ENDPOINTS_PATTERN };
