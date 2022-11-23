const actions = [
  '/pipelines',
  '/pipeline/:id',
  '/client/new',
  '/client/:id',
  '/clients',
  '/user/new',
  '/user/:id',
  '/users',
  '/site/new',
  '/site/:id',
  '/sites',
  '/building/new',
  '/building/:id',
  '/buildings',
  '/floor/new',
  '/floor/plan',
  '/floor/:id',
  '/floors',
  '/units',
  '/profile',
  'run_simulations',
] as const;

export type ActionsType = typeof actions[number];

export default actions;
