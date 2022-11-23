const actions = [
  '/projects',
  '/qa/:siteId',
  '/competitions',
  '/competition/:id',
  'competition:change-weights',
  'competition:change-competitor-raw-data',
] as const;

export type ActionsType = typeof actions[number];

export default actions;
