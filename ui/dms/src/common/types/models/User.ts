import { RolesType } from '..';

type UserModel = {
  client_id: number;
  created: string;
  group_id: number;
  id: number;
  login: string;
  name: string;
  email: string;
  roles: RolesType[];
  updated: string;
};

export default UserModel;
