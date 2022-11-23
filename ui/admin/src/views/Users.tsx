import React from 'react';
import useSWR from 'swr';
import { Admin, LinkRenderer } from '../components';
import { C } from '../common';
import { ProviderRequest } from '../providers';

const columns = [
  {
    headerName: 'ID',
    field: 'id',
    filter: true,
    sortable: true,
  },
  {
    headerName: 'Client',
    field: 'client',
    filter: true,
    sortable: true,
  },
  {
    headerName: 'Login',
    field: 'login',
    filter: true,
    sortable: true,
  },
  {
    headerName: 'Name',
    field: 'name',
    filter: true,
    sortable: true,
  },
  {
    headerName: 'Email',
    field: 'email',
    filter: true,
    sortable: true,
  },
  {
    headerName: 'Roles',
    field: 'roles',
    filter: true,
    sortable: true,
  },
  {
    headerName: 'Last Login',
    field: 'last_login',
    filter: false,
    sortable: true,
  },
  {
    headerName: 'Email Validated',
    field: 'email_validated',
    filter: false,
    sortable: true,
  },
  {
    headerName: '',
    field: 'actions',
    cellRendererFramework: ({ data }) => <LinkRenderer id={data.id} href={`/user/${data.id}`} text={'Edit'} />,
    maxWidth: 90,
  },
];

const parseRows = (users, clients) => {
  const clientsPerId = clients.reduce((accum, client) => {
    accum[client.id] = client;
    return accum;
  }, {});

  return users.map(user => {
    const { client_id, ...rest } = user;
    return {
      client: clientsPerId[client_id] && clientsPerId[client_id].name,
      ...rest,
    };
  });
};

const Users = () => {
  const { data: users = [] } = useSWR(C.ENDPOINTS.USER(), ProviderRequest.get);
  const { data: clients = [] } = useSWR(C.ENDPOINTS.CLIENT(), ProviderRequest.get);
  const rows = parseRows(users, clients);
  return <Admin rows={rows} columns={columns} id={'users_table'} allowCreation />;
};
export default Users;
