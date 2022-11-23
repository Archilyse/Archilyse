import * as React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { C } from '../../../../common';
import Grid from './Grid';

afterEach(cleanup);

const { PDF, PNG, JPEG } = C.MIME_TYPES;
const { DXF, IFC } = C.FILE_EXTENSIONS;

const MOCK_FILES = [
  { name: 'floorplan1', type: JPEG, id: 1 },
  { name: 'floorplan3', type: JPEG, id: 2 },
  { name: 'floorplan4', type: JPEG, id: 3 },
  { name: 'sample floorplan', type: JPEG, id: 4 },
  { name: 'dxf', type: DXF, id: 5 },
  { name: 'some ifc', type: IFC, id: 6 },
  { name: 'floorplan5', type: PDF, id: 7 },
  { name: 'sample png', type: PNG, id: 8 },
  { name: 'another pdf', type: PDF, id: 9 },
];

const MOCK_FOLDERS = [
  { id: 63, name: 'Bearingpoint Corona Dashboard', type: 'folder-clients' },
  { id: 4, name: 'cemex', type: 'folder-clients' },
  { id: 8, name: 'Migros', type: 'folder-clients' },
  { id: 9, name: 'Viva Real', type: 'folder-clients' },
  { id: 10, name: 'Property Quants', type: 'folder-clients' },
  { id: 11, name: 'Midwood', type: 'folder-clients' },
  { id: 12, name: 'BWO', type: 'folder-clients' },
  { id: 14, name: 'Immobilien Basel-Stadt', type: 'folder-clients' },
  { id: 18, name: 'HMQ', type: 'folder-clients' },
  { id: 20, name: 'Credit Suisse', type: 'folder-clients' },
  { id: 13, name: 'FSP', type: 'folder-clients' },
  { id: 19, name: 'Bluewin', type: 'folder-clients' },
  { id: 1, name: 'Portfolio Client', type: 'folder-clients' },
];

jest.mock('react-virtualized-auto-sizer', () => ({ children }) => children({ height: 1000, width: 1000 }));

const MOCK_DATA = [...MOCK_FOLDERS, ...MOCK_FILES];

it('renders correctly with no data', () => {
  render(
    <MemoryRouter>
      <Grid
        pathname={C.DMS_VIEWS.SITES}
        onClickCustomFolder={() => {}}
        data={[]}
        onClickFolder={() => {}}
        onClickFile={() => {}}
        onContextMenu={() => {}}
        onMouseEnter={() => {}}
        onMouseLeave={() => {}}
        itemInClipboard={null}
      />
    </MemoryRouter>
  );
  expect(screen.getByTestId('dms-grid')).toBeInTheDocument();
});

it('renders correctly with folders & files', () => {
  render(
    <MemoryRouter>
      <Grid
        pathname={C.DMS_VIEWS.SITES}
        onClickCustomFolder={() => {}}
        data={MOCK_DATA}
        onClickFolder={() => {}}
        onClickFile={() => {}}
        onContextMenu={() => {}}
        onMouseEnter={() => {}}
        onMouseLeave={() => {}}
        itemInClipboard={null}
      />
    </MemoryRouter>
  );

  for (const item of MOCK_DATA) {
    expect(screen.getAllByText(new RegExp(item.name))).toBeTruthy();
  }
});
