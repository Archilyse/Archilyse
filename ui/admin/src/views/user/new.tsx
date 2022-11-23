import React from 'react';
import useSWR from 'swr';
import EntityView from '../../components/EntityView';
import formFields from '../../common/forms/user';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';

const parseForm = (formFields, clients, groups, roles = []) =>
  formFields.map(field => {
    if (field.name === 'client_id') {
      field.options = (clients || []).map(client => ({ label: client.name, value: client.id }));
    } else if (field.name === 'roles') {
      field.options = (roles || []).map(r => ({ label: r.role, value: r.role }));
    } else if (field.name === 'group_id') {
      field.options = (groups || []).map(group => ({ label: group.name, value: group.id }));
    }
    if (field.options && !field.multiple) {
      field.options.unshift({ value: '', label: C.FORMS.EMPTY_LABEL });
    }
    return field;
  });

const User = () => {
  const { data: clients = [] } = useSWR(C.ENDPOINTS.CLIENT(), ProviderRequest.get);
  const { data: groups = [] } = useSWR(C.ENDPOINTS.GROUP(), ProviderRequest.get);
  const { data: roles = [] } = useSWR(C.ENDPOINTS.USER_ROLES(), ProviderRequest.get);
  const fields = parseForm(formFields, clients, groups, roles);
  return <EntityView fields={fields} entity={{}} parent={{}} context="user" />;
};
export default User;
