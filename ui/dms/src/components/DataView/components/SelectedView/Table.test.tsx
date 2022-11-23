import * as React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { C } from '../../../../common';
import Table from './Table';

afterEach(cleanup);

const { PDF, PNG, JPEG } = C.MIME_TYPES;

const { DXF, IFC } = C.FILE_EXTENSIONS;
const { SITES, CLIENTS, BUILDINGS, FLOORS, UNITS, ROOMS, TRASH } = C.DMS_VIEWS;

const MOCK_CREATION_DATE = '2020-08-27T09:47:17.780Z';

const MOCK_FOLDERS = [
  { id: 63, name: 'Folder 1', created: MOCK_CREATION_DATE, type: 'custom-folder' },
  { id: 8, name: 'Folder 2', created: MOCK_CREATION_DATE, type: 'custom-folder' },
];
const MOCK_FILES = [
  { name: 'floorplan1', type: JPEG, labels: [], created: MOCK_CREATION_DATE, id: 1 },
  { name: 'sample_floorplan', type: PNG, labels: [], created: MOCK_CREATION_DATE, id: 2 },
  { name: 'sample_dxf', type: DXF, labels: [], created: MOCK_CREATION_DATE, id: 3 },
  { name: 'sample_ifc', type: IFC, labels: [], created: MOCK_CREATION_DATE, id: 4 },
  { name: 'another_pdf', type: PDF, created: MOCK_CREATION_DATE, id: 5 },
];

const MOCK_CLIENTS = [{ name: 'clientaso', type: 'folder-clients', id: 2 }];
const MOCK_SITES = [{ name: 'chosaso', type: 'folder-sites', id: 2, labels: ['papaya'] }];
const MOCK_BUILDINGS = [{ name: 'chosaso_building', type: 'folder-buildings', id: 2, labels: ['aguacate'] }];
const MOCK_FLOORS = [{ name: 'Floor 0', type: 'folder-floors', id: 1, labels: ['kiwi'] }];
const MOCK_UNITS = [{ name: 'Unit toa_pasa_de_rosca_001', type: 'folder-units', id: 1, labels: [] }];
const MOCK_ROOMS = [
  { name: 'Kitchen 1', type: 'folder-rooms', id: 1 },
  { name: 'Room 1', type: 'folder-rooms', id: 2 },
];
const MOCK_TRASH = [{ name: 'clientaso', type: 'folder-clients', updated: '2022-11-14T15:54:17.645074' }];

const getByTextIngoringHidden = (text: string | RegExp) => {
  // @ts-ignore
  return screen.getByText(text, { ignore: "[aria-hidden='true']" });
};

let mockPathname;
jest.mock('../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
  usePrevious: () => {},
  useWindowSize: () => {},
}));
jest.mock('react-virtualized-auto-sizer', () => ({ children }) => children({ height: 1000, width: 1000 }));

const MOCK_DATA = [...MOCK_FOLDERS, ...MOCK_FILES];

describe('Table component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<Table {...props} />);
  };
  beforeEach(() => {
    mockPathname = SITES;
    props = {
      pathname: SITES,
      data: [],
      onClickFolder: () => {},
      onClickCustomFolder: () => {},
      onClickFile: () => {},
      onChangeTags: () => {},
      onContextMenu: () => {},
      onMouseEnter: () => {},
      onMouseLeave: () => {},
      itemInClipboard: null,
    };
  });

  it('renders correctly with no data', () => {
    renderComponent();
    expect(screen.getByTestId('dms-table')).toBeInTheDocument();
  });

  it('renders correctly with data, and sorts files properly', () => {
    renderComponent({ data: MOCK_DATA });
    for (const item of MOCK_DATA) {
      expect(getByTextIngoringHidden(new RegExp(item.name))).toBeInTheDocument();
    }
    // Sort by name
    fireEvent.click(screen.getByTestId('name'));
    for (const item of MOCK_DATA) {
      expect(getByTextIngoringHidden(new RegExp(item.name))).toBeInTheDocument();
    }
  });

  it('renders in trash view, with the expiry date', () => {
    renderComponent({ pathname: TRASH, data: MOCK_TRASH });
    expect(screen.queryByText(/Expiry Date/)).toBeTruthy();
    expect(screen.queryByText('12/14/2022, 3:54:17 PM')).toBeInTheDocument();
  });

  describe('Tags', () => {
    it.each([
      ['sites', SITES, MOCK_SITES],
      ['buildings', BUILDINGS, MOCK_BUILDINGS],
      ['floors', FLOORS, MOCK_FLOORS],
      ['units', UNITS, MOCK_UNITS],
      ['rooms', ROOMS, MOCK_ROOMS],
      ['folders', SITES, MOCK_FOLDERS],
      ['files', SITES, MOCK_FILES],
    ])('Are rendered for %s', async (entityName, pathname, mockData) => {
      mockPathname = pathname;
      renderComponent({ pathname, data: mockData });
      const hasTags = screen.queryAllByTestId('tags-text-field').length > 0;
      expect(hasTags).toBeTruthy();
    });

    it.each([['clients', CLIENTS, MOCK_CLIENTS]])('Are not rendered for %s', async (entityName, pathname, mockData) => {
      mockPathname = pathname;
      renderComponent({ pathname: pathname, data: mockData });
      const hasTags = screen.queryAllByTestId('tags-text-field').length > 0;
      expect(hasTags).toBeFalsy();
    });
  });

  describe('PH Values', () => {
    it.each([
      ['floors', FLOORS, MOCK_FLOORS],
      ['units', UNITS, MOCK_UNITS],
    ])('Are displayed appropriately with no NaN values', async (entityName, pathname, mockData) => {
      mockPathname = pathname;
      renderComponent({ pathname, data: mockData });
      const hasInvalidValues = screen.queryAllByText(/(NaN%?) | (0.00%)/).length > 0;
      expect(hasInvalidValues).toBeFalsy();
    });
  });
});
