import { getUserRoles } from 'archilyse-ui-components';
import PERMISSIONS from './permissions';
import { ActionsType } from './actions';

export default function checkAccess(action: ActionsType | ActionsType[]): boolean {
  const roles = getUserRoles();

  if (roles.length === 0) {
    return false;
  }

  if (Array.isArray(action)) {
    return action.every(item => checkAccess(item));
  }

  return roles.some(role => {
    if (!PERMISSIONS[role]) return false;
    // empty array ([]) mean user can do anything
    if (PERMISSIONS[role].length === 0) {
      return true;
    }

    return PERMISSIONS[role].includes(action);
  });
}
