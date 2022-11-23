import { getUserRoles } from 'archilyse-ui-components';
import { C } from '..';

const { ADMIN, COMPETITION_ADMIN, COMPETITION_VIEWER } = C.ROLES;
const { URLS } = C;

const DEFAULT_QA_SITE = 1440; // Using a real site by default

export default function getInitialPageUrlByRole() {
  const userRole: string[] = getUserRoles();

  if (userRole.length === 0) {
    return URLS.LOGIN();
  }

  if (userRole.includes(ADMIN)) {
    return C.URLS.QA(DEFAULT_QA_SITE);
  } else if (userRole.includes(COMPETITION_ADMIN) || userRole.includes(COMPETITION_VIEWER)) {
    return URLS.COMPETITIONS();
  } else {
    return URLS.LOGIN();
  }
}
