import * as React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import DataView from '.';

afterEach(cleanup);

const MOCK_CLIENTS = [
  { id: 63, name: 'Bearingpoint Corona Dashboard' },
  { id: 4, name: 'cemex' },
  { id: 8, name: 'Migros' },
];

jest.mock('react-virtualized-auto-sizer', () => ({ children }) => children({ height: 1000, width: 1000 }));
window.URL.createObjectURL = jest.fn(() => 'blob:http://localhost:9000/2b9be933-9b4f-4ec5-9d16-337423936ff9');

describe('Dataview component', () => {
  beforeEach(() => {
    MOCK_AUTHENTICATION();
  });

  it('renders correctly a table with mock data by default', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/clients']}>
        <DataView data={MOCK_CLIENTS} onClickFolder={() => {}} />
      </MemoryRouter>
    );
    await waitFor(() => container.querySelector('.selected-view.table'));
  });

  it('renders correctly a table by default and we can switch between views', async () => {
    const { container, getByTestId } = render(
      <MemoryRouter initialEntries={['/clients']}>
        <DataView data={MOCK_CLIENTS} onClickFolder={() => {}} />
      </MemoryRouter>
    );

    await waitFor(() => container.querySelector('.selected-view.table'));

    // Switch back to grid view
    fireEvent.click(getByTestId('toggle-view'));
    expect(container.querySelector('.folder')).toBeInTheDocument();

    // Switch back to table view
    fireEvent.click(getByTestId('toggle-view'));
    expect(container.querySelector('.dms-table')).toBeInTheDocument();
  });

  it('renders correctly the breadcrumb with a folder created inside a floor', async () => {
    const nodeListToArray = nodeList => Array.prototype.slice.call(nodeList);

    render(
      <MemoryRouter initialEntries={['/custom_folder?folder_id=1']}>
        <DataView data={[]} />
      </MemoryRouter>
    );
    const isBreadcrumbLoaded = () => nodeListToArray(screen.queryAllByText(/Folder/)).length > 0;
    await waitFor(() => expect(isBreadcrumbLoaded()).toBeTruthy());

    // Ensure all levels are shown in the hierarchy/breadcrumb
    expect(screen.getAllByText(/All Clients/)).toBeTruthy();
    expect(screen.getAllByText(/Site/)).toBeTruthy();
    expect(screen.getAllByText(/Building/)).toBeTruthy();
    expect(screen.getAllByText(/Floor/)).toBeTruthy();
    expect(screen.getAllByText(/Folder/)).toBeTruthy();
  });
});
