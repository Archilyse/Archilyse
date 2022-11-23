import { auth } from 'archilyse-ui-components';
import getEntityId from './getEntityId';

export default (hierarchy, query) => {
  const { client_id } = auth.getUserInfo();
  if (client_id) return client_id;
  // If we don't find it in the user token info, it can be in the query or hierarchy if it is an admin
  if (query.client_id) return query.client_id;
  return getEntityId(hierarchy, 'client_id');
};
