import C from '../constants';
import { RolesType } from '../types';
import { ActionsType } from './actions';

const { ADMIN, COMPETITION_ADMIN, COMPETITION_VIEWER } = C.ROLES;

const permissions: PermissionsType = {
  [ADMIN]: [],
  [COMPETITION_ADMIN]: ['/competitions', '/competition/:id', 'competition:change-weights'],
  [COMPETITION_VIEWER]: ['/competitions', '/competition/:id'],
};

export type PermissionsType = {
  [role in RolesType]: ActionsType[];
};

export default permissions;
