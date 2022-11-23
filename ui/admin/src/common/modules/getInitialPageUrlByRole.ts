import { auth } from 'archilyse-ui-components';
import { C } from '..';

const { ADMIN } = C.ROLES;
const { URLS } = C;

export default function getInitialPageUrlByRole() {
  const userRole = auth.getRoles();

  if (!userRole) {
    return URLS.CLIENTS();
  }

  if (userRole.includes(ADMIN)) {
    return URLS.CLIENTS();
  } else {
    return URLS.CLIENTS(); // temporary for others roles
  }
}
