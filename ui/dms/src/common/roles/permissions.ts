import C from '../constants';
import { ActionsType } from './actions';

const { ROLES } = C;
const { ADMIN, ARCHILYSE_ONE_ADMIN, DMS_LIMITED } = C.ROLES;

const VIEWS = Object.values(C.DMS_VIEWS).filter(view => view !== '/clients');

const permissions: PermissionsType = {
  [ADMIN]: [],
  [ARCHILYSE_ONE_ADMIN]: [...VIEWS, '/profile', 'go_to_rent_calibrator'],
  [DMS_LIMITED]: [...VIEWS, '/profile'],
};

type RolesType = typeof ROLES[keyof typeof ROLES];
export type PermissionsType = {
  [role in RolesType]: ActionsType[];
};

export default permissions;
