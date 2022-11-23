import C from '../constants';

const VIEWS = Object.values(C.DMS_VIEWS);

const actions = ['/profile', 'go_to_rent_calibrator', ...VIEWS] as const;
export type ActionsType = typeof actions[number];

export default actions;
