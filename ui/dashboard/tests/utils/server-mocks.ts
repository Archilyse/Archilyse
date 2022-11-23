import { RequestHandler, rest } from 'msw';
import { setupServer } from 'msw/node';
import { C } from '../../src/common';
import {
  CompetitionConfigurationParamsResponseType,
  CompetitionMainCategoryResponseType,
  CompetitionScoresResponseType,
  CompetitionType,
  CompetitionWeightsResponseType,
  CompetitorResponseType,
  CompetitorsUnitsResponse,
} from '../../src/common/types';
import competition from '../../src/views/Competition/__fixtures__/competition';

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

const { UNIT_HEATMAPS } = C.ENDPOINTS;

const UNIT_HEATMAPS_WITHOUT_QUERY = UNIT_HEATMAPS(anyNumber).substring(0, UNIT_HEATMAPS(anyNumber).indexOf('?'));

const patterns = {
  COMPETITION_CATEGORIES: new RegExp(C.ENDPOINTS.COMPETITION_CATEGORIES(anyNumber)),
  COMPETITION_INFO: new RegExp(C.ENDPOINTS.COMPETITION_INFO(anyNumber) + '$'),
  COMPETITION_WEIGHTS: new RegExp(C.ENDPOINTS.COMPETITION_WEIGHTS(anyNumber)),
  COMPETITION_COMPETITORS: new RegExp(C.ENDPOINTS.COMPETITION_COMPETITORS(anyNumber) + '$'),
  COMPETITION_COMPETITORS_UNITS: new RegExp(C.ENDPOINTS.COMPETITION_COMPETITORS_UNITS(anyNumber)),
  COMPETITION_SCORES: new RegExp(C.ENDPOINTS.COMPETITION_SCORES(anyNumber)),
  COMPETITION_PARAMETERS: new RegExp(C.ENDPOINTS.COMPETITION_PARAMETERS(anyNumber)),

  SITE: new RegExp(C.ENDPOINTS.SITE(anyNumber) + '$'),
  SITE_STRUCTURE: new RegExp(C.ENDPOINTS.SITE_STRUCTURE(anyNumber)),
  SITE_UNITS: new RegExp(C.ENDPOINTS.SITE_UNITS(anyNumber)),
  SITE_SIM_VALIDATION: new RegExp(C.ENDPOINTS.SITE_SIM_VALIDATION(anyNumber)),

  UNIT_HEATMAPS: new RegExp(UNIT_HEATMAPS_WITHOUT_QUERY),

  PLAN: new RegExp(C.ENDPOINTS.PLAN(anyNumber)),
  FLOOR: new RegExp(C.ENDPOINTS.FLOOR(anyNumber)),
};

const handlers = [
  buildHandler<CompetitionMainCategoryResponseType[]>(patterns.COMPETITION_CATEGORIES, 'get', []),
  buildHandler<CompetitionType>(patterns.COMPETITION_INFO, 'get', competition),
  buildHandler<CompetitionWeightsResponseType>(patterns.COMPETITION_WEIGHTS, 'get', null),
  buildHandler<CompetitorsUnitsResponse[]>(patterns.COMPETITION_COMPETITORS_UNITS, 'get', []),
  buildHandler<CompetitorResponseType[]>(patterns.COMPETITION_COMPETITORS, 'get', []),
  buildHandler<CompetitionScoresResponseType[]>(patterns.COMPETITION_SCORES, 'get', []),

  buildHandler<CompetitionConfigurationParamsResponseType>(patterns.COMPETITION_PARAMETERS, 'get', {
    flat_types_distribution: [],
    showers_bathtubs_distribution: [],
  }),
  buildHandler<CompetitionConfigurationParamsResponseType>(patterns.COMPETITION_PARAMETERS, 'put', {
    flat_types_distribution: [],
    showers_bathtubs_distribution: [],
  }),

  buildHandler(patterns.SITE, 'get', null),
  buildHandler(patterns.SITE_STRUCTURE, 'get', null),
  buildHandler(patterns.SITE_UNITS, 'get', null),
  buildHandler(patterns.SITE_SIM_VALIDATION, 'get', null),

  buildHandler(patterns.UNIT_HEATMAPS, 'get', null),

  buildHandler(patterns.FLOOR, 'get', null),
  buildHandler(patterns.PLAN, 'get', null),
];

const server = setupServer(...handlers);

export { server, buildHandler, patterns as ENDPOINTS_PATTERN };
