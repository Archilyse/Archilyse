import { RequestHandler, rest } from 'msw';
import { setupServer } from 'msw/node';
import { siteStructure } from '../../src/components/HeatmapModalContent/__fixtures__/siteStructure';
import { units } from '../../src/components/HeatmapModalContent/__fixtures__/units';
import C from '../../src/constants';

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

const UNIT_HEATMAPS_WITHOUT_QUERY = C.ENDPOINTS.UNIT_HEATMAPS(anyNumber).substring(
  0,
  C.ENDPOINTS.UNIT_HEATMAPS(anyNumber).indexOf('?')
);

const patterns = {
  SITE_STRUCTURE: new RegExp(C.ENDPOINTS.SITE_STRUCTURE(anyNumber)),
  SITE_UNITS: new RegExp(C.ENDPOINTS.SITE_UNITS(anyNumber)),

  UNIT_HEATMAPS: new RegExp(UNIT_HEATMAPS_WITHOUT_QUERY),
};

const handlers = [
  buildHandler(patterns.SITE_STRUCTURE, 'get', siteStructure),
  buildHandler(patterns.SITE_UNITS, 'get', units),
  buildHandler(patterns.UNIT_HEATMAPS, 'get', null),
];

const server = setupServer(...handlers);

export { server, buildHandler, patterns as ENDPOINTS_PATTERN };
