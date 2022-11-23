/* Parse backend rules of all users to the format expected by the UI */

import { BackendRules, Rules, Site } from 'Common/types';

type RawRules = {
  [userId: string]: {
    [permission: string]: Site[];
  };
};

const parseBackendRules = (permissions: BackendRules, sites: Site[]): Rules => {
  const rawRules: RawRules = {};
  permissions.forEach(permission => {
    const currentSite: Site = sites.find(s => s.id === permission.site_id);
    rawRules[permission.user_id] = rawRules[permission.user_id] || { [permission.rights]: [] };
    rawRules[permission.user_id][permission.rights] = rawRules[permission.user_id][permission.rights] || [];
    rawRules[permission.user_id][permission.rights].push(currentSite);
  });

  const result = {};
  Object.entries(rawRules).forEach(([userId, rule]) => {
    result[userId] = result[userId] || [];
    result[userId] = Object.entries(rule).map(([permission, sites]) => ({ permission, sites }));
  });
  return result;
};

export default parseBackendRules;
