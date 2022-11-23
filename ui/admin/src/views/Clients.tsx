import React, { useContext, useState } from 'react';
import useSWR from 'swr';
import { auth, SnackbarContext } from 'archilyse-ui-components';
import { Checkbox } from '@material-ui/core';
import { Admin, LinkRenderer } from '../components';
import { ProviderRequest } from '../providers';
import { C } from '../common';

const CheckBoxRenderer = (data, columns, field) => {
  const [checked, setChecked] = useState(Boolean(columns.reduce((state, column) => state && data[column], true)));

  const snackbar = useContext(SnackbarContext);

  const changeCheckboxStatus = async () => {
    const newChecked = !checked;
    setChecked(newChecked);

    try {
      const payload = Object.assign({}, ...columns.map(col => ({ [col]: newChecked })));
      await ProviderRequest.put(C.ENDPOINTS.CLIENT(data.id), payload);
    } catch (error) {
      snackbar.show({ message: `Error saving ${field} status: ${error}`, severity: 'error' });
    }
  };

  return (
    <Checkbox
      checked={checked}
      color="primary"
      className={`${field}-${checked}`}
      onChange={changeCheckboxStatus}
      value="primary"
      inputProps={{ 'aria-label': 'primary checkbox' }}
    />
  );
};
const getColumns = (checkBoxRenderer, roles) => {
  let columns: any = [
    {
      headerName: 'ID',
      field: 'id',
      filter: true,
      sortable: true,
      maxWidth: 80,
    },
    {
      headerName: 'Name',
      field: 'name',
      filter: true,
      sortable: true,
      resizable: true,
      cellClass: 'client-name',
    },
    {
      headerName: 'Sites',
      field: 'sites',
      cellRendererFramework: ({ data }) => (
        <LinkRenderer id={data.id} href={C.URLS.SITES_BY_CLIENT(data.id)} text={'Sites'} />
      ),
      maxWidth: 100,
    },
    {
      headerName: 'Competitions',
      field: 'competitions',
      cellRendererFramework: ({ data }) => (
        <LinkRenderer
          id={`[data.id]-competitions`}
          href={C.URLS.COMPETITIONS_BY_CLIENT(data.id)}
          text={'Competitions'}
        />
      ),
      maxWidth: 100,
    },
  ];

  if (roles && roles.includes(C.ROLES.ADMIN)) {
    columns.push(
      {
        headerName: 'Full Package',
        columns: ['option_dxf', 'option_pdf', 'option_analysis', 'option_ifc'],
        default: true,
        cellRendererFramework: ({ data, colDef }) => CheckBoxRenderer(data, colDef.columns, 'option_full_package'),
        maxWidth: 90,
      },
      {
        headerName: '',
        field: 'actions',
        cellRendererFramework: ({ data }) => <LinkRenderer id={data.id} href={`/client/${data.id}`} text={'Edit'} />,
        width: 70,
      }
    );
  }

  columns = columns.map(c => ({
    filter: true,
    sortable: true,
    resizable: true,
    ...c,
  }));
  return columns;
};

const Clients = () => {
  const { data: clients } = useSWR(C.ENDPOINTS.CLIENT(), ProviderRequest.get);
  const roles = auth.getRoles();

  const columns = getColumns(CheckBoxRenderer, roles);

  return <Admin rows={clients} id={'clients_table'} columns={columns} allowCreation />;
};

export default Clients;
