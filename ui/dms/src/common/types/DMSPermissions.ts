import C from '../constants';

const { DMS_PERMISSIONS } = C;

type DMS_Permissions = typeof DMS_PERMISSIONS[keyof typeof DMS_PERMISSIONS];

export default DMS_Permissions;
