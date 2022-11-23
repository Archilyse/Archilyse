import { C } from 'Common';
import { Rule } from 'Common/types';

const { DMS_PERMISSIONS } = C;
const { READ_ALL, EDIT_ALL } = DMS_PERMISSIONS;

const getPermissionName = permission =>
  Object.keys(DMS_PERMISSIONS)
    .find(label => DMS_PERMISSIONS[label] === permission)
    ?.toLowerCase();

const getRuleName = ({ permission, sites }: Rule): string => {
  if (permission === READ_ALL || permission === EDIT_ALL) {
    return permission.replace('_', ' '); // @TODO: Capitalize
  }
  return `${getPermissionName(permission)}:${sites.map(s => s?.name).join(',')}`;
};

export default getRuleName;
