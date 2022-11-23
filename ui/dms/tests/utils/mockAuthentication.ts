import { auth } from 'archilyse-ui-components';
import { C } from 'Common';

type RolesType = typeof C.ROLES[keyof typeof C.ROLES];

export default (role: RolesType = C.ROLES.ADMIN) => {
  // This token needs to have the client_id field set so that the unitests receive the data required
  const mockToken =
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYyNTUyOTYwMCwianRpIjoiNTg1MWM1MmQtODE5OS00NmZjLWEzYWUtN2ZhZDk2ZDVlZTc4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiZ3JvdXBfaWQiOjEsImNsaWVudF9pZCI6MX0sIm5iZiI6MTYyNTUyOTYwMCwiZXhwIjoxNjI2ODI1NjAwfQ.YDxZYTD3JNxltceJKEfgPHF0_Ngt-YDeVb9f-3XIRzY';
  const mockRoles = [role];
  auth.authenticate(mockToken, mockRoles);
};
