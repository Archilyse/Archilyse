import DMSPermissions from './DMSPermissions';
import Site from './models/Site';

type Rule = {
  sites: Site[];
  permission: DMSPermissions;
};

export default Rule;
