/*  Compile user rules to the format expect by the backend on a update */

import { DMSPermissions, Rule } from 'Common/types';
import { C } from 'Common';

const { READ_ALL, EDIT_ALL } = C.DMS_PERMISSIONS;
type backendUpdateRules = {
  site_id: number;
  rights: DMSPermissions;
}[];

const compileUserRules = (userRules: Rule[]): backendUpdateRules => {
  const backendRules = [];
  userRules.forEach(rule => {
    if (rule.permission === READ_ALL || rule.permission === EDIT_ALL) {
      backendRules.push({ rights: rule.permission });
      return;
    }
    rule.sites.forEach(site => {
      backendRules.push({ rights: rule.permission, site_id: site.id });
    });
  });
  return backendRules;
};

export default compileUserRules;
