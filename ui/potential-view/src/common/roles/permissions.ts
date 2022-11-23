import { C } from '..';
import { RolesType } from '../types';
import { ActionsType } from './actions';

const permissions: PermissionsType = {
  [C.ROLES.ADMIN]: [],
  [C.ROLES.POTENTIAL_API]: ['/', '/:id'],
};

export type PermissionsType = {
  [role in RolesType]: ActionsType[];
};

export default permissions;
