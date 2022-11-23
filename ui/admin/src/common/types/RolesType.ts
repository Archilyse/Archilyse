import C from '../constants';

const { ROLES } = C;

type RolesType = typeof ROLES[keyof typeof ROLES];

export default RolesType;
