import { auth } from 'archilyse-ui-components';
import { ROLES } from '../../constants';

type RolesType = typeof ROLES[keyof typeof ROLES];

export default (role: RolesType = ROLES.ADMIN) => {
  const mockToken =
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYyNTUyOTYwMCwianRpIjoiNTg1MWM1MmQtODE5OS00NmZjLWEzYWUtN2ZhZDk2ZDVlZTc4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiZ3JvdXBfaWQiOjEsImNsaWVudF9pZCI6MX0sIm5iZiI6MTYyNTUyOTYwMCwiZXhwIjoxNjI2ODI1NjAwfQ.YDxZYTD3JNxltceJKEfgPHF0_Ngt-YDeVb9f-3XIRzY';
  const mockRoles = [role];
  auth.authenticate(mockToken, mockRoles);
};
