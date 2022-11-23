import * as React from 'react';
import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { C } from 'Common';
import { renderWithRouter } from '../../tests/utils';
import MOCK_CLIENTS from '../../__mocks__/entities/clients.js';

import Admin from './Admin';

const MOCK_COLUMNS = [
  {
    filter: true,
    sortable: true,
    resizable: true,
    headerName: 'ID',
    field: 'id',
    maxWidth: 80,
  },
  {
    filter: true,
    sortable: true,
    resizable: true,
    headerName: 'Name',
    field: 'name',
    cellClass: 'client-name',
  },
  {
    filter: true,
    sortable: true,
    resizable: true,
    headerName: 'Sites',
    field: 'sites',
    maxWidth: 100,
  },
];

describe('Admin component', () => {
  let props;
  const renderComponent = (changedProps = {}, route) => {
    props = { ...props, ...changedProps };
    return renderWithRouter(<Admin {...props} />, route);
  };
  beforeEach(() => {
    props = {
      rows: MOCK_CLIENTS,
      id: 'clients_table',
      columns: MOCK_COLUMNS,
      allowCreation: true,
    };
  });

  const waitForLoad = async () =>
    waitFor(() => expect(screen.getByText(MOCK_COLUMNS[0].headerName)).toBeInTheDocument());

  it('Renders correctly mock data', async () => {
    renderComponent({}, C.URLS.CLIENTS());

    await waitForLoad();

    MOCK_COLUMNS.forEach(column => {
      expect(screen.getByText(new RegExp(column.headerName))).toBeInTheDocument();
    });

    // Client values are there
    MOCK_CLIENTS.forEach(client => {
      expect(screen.getByRole('gridcell', { name: client.id })).toBeInTheDocument();
      expect(screen.getByRole('gridcell', { name: client.name })).toBeInTheDocument();
    });
  });

  it('Filters the data on introducing a search term', async () => {
    renderComponent({}, C.URLS.CLIENTS());
    await waitForLoad();

    // Initially all clients are there
    MOCK_CLIENTS.forEach(client => {
      expect(screen.getByRole('gridcell', { name: client.id })).toBeInTheDocument();
      expect(screen.getByRole('gridcell', { name: client.name })).toBeInTheDocument();
    });

    // Filter a client and waits for removal
    const filteredClient = MOCK_CLIENTS[0].name;
    userEvent.type(screen.getByRole('searchbox'), filteredClient);

    const otherClient = new RegExp(MOCK_CLIENTS[1].name);
    await waitForElementToBeRemoved(() => screen.queryByText(otherClient));

    // Only the filtered client is visible
    MOCK_CLIENTS.forEach(client => {
      if (client.name === filteredClient) {
        expect(screen.queryByText(new RegExp(filteredClient))).toBeInTheDocument();
      } else {
        expect(screen.queryByText(new RegExp(client.name))).not.toBeInTheDocument();
      }
    });
  });
});
