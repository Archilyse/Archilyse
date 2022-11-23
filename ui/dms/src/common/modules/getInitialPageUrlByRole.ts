import { auth } from 'archilyse-ui-components';
import { C } from '..';

const { ADMIN, ARCHILYSE_ONE_ADMIN, DMS_LIMITED } = C.ROLES;
const { URLS } = C;

export default function getInitialPageUrlByRole() {
  const userRole = auth.getRoles();

  if (!userRole) {
    return URLS.CLIENTS();
  }

  if (userRole.includes(ADMIN)) {
    return URLS.CLIENTS();
  } else if (userRole.includes(ARCHILYSE_ONE_ADMIN) || userRole.includes(DMS_LIMITED)) {
    const { client_id } = auth.getUserInfo();

    return URLS.SITES_BY_CLIENT(client_id);
  } else {
    return URLS.CLIENTS(); // temporary for others roles
  }
}
