const actions = ['/', '/:id', 'simulations-list'] as const;

export type ActionsType = typeof actions[number];

export default actions;
