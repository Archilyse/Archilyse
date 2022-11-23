import DMS_Permissions from './DMSPermissions';

type BackendRules = { site_id: number; rights: DMS_Permissions; user_id: number }[];

export default BackendRules;
