import C from '../constants';
import { ActionsType } from './actions';

const { ROLES } = C;
const { ADMIN, TEAMMEMBER, TEAMLEADER } = C.ROLES;

const base_permissions: ActionsType[] = [
  '/pipelines',
  '/pipeline/:id',
  '/client/new',
  '/client/:id',
  '/clients',
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
];
const permissions: PermissionsType = {
  [ADMIN]: [],
  [TEAMMEMBER]: base_permissions,
  [TEAMLEADER]: base_permissions.concat(['/clients', 'run_simulations']),
};

type RolesType = typeof ROLES[keyof typeof ROLES];
export type PermissionsType = {
  [role in RolesType]: ActionsType[];
};

export default permissions;
