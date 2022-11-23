import { C } from '../../common';

type RolesType = typeof C.ROLES[keyof typeof C.ROLES];

export default RolesType;
