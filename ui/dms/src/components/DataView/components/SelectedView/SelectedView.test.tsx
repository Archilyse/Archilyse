import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getRoomName } from 'Common/modules';
import { C } from '../../../../common';
import SelectedView from '.';

const { SITES, CLIENTS, BUILDINGS, FLOORS, UNITS, ROOMS, ROOM, CUSTOM_FOLDER, TRASH } = C.DMS_VIEWS;

const { PDF, JPEG } = C.MIME_TYPES;
const { IFC } = C.FILE_EXTENSIONS;

type DMSView = typeof C.DMS_VIEWS[keyof typeof C.DMS_VIEWS];

const MOCK_FILES = [
  { name: 'plan1', content_type: JPEG, id: 1 },
  { name: 'plan2', content_type: JPEG, id: 2 },
  { name: 'sample_ifc', content_type: IFC, id: 6, labels: ['avocado'] },
  { name: 'another_pdf', content_type: PDF, id: 9, labels: ['pineapple', 'tomato'] },
];

const MOCK_FOLDERS = [{ name: 'super-folder', type: C.CUSTOM_FOLDER_TYPE, id: 1 }];

const MOCK_SITES = [{ name: 'chosaso', type: 'folder-sites', id: 2, labels: ['papaya'] }];

const MOCK_COMPLETED_SITE = {
  id: 1,
  full_slam_results: C.STATUS.SUCCESS,
  heatmaps_qa_complete: true,
};

const getByTextIngoringHidden = (text: string | RegExp) => {
  // @ts-ignore
  return screen.getByText(text, { ignore: "[aria-hidden='true']" });
};

let mockPathname;
jest.mock('../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname, query: { floor_id: 100 } }),
  usePrevious: () => {},
  useWindowSize: () => ({}),
}));

jest.mock('react-virtualized-auto-sizer', () => ({ children }) => children({ height: 1000, width: 600 }));

jest.mock('./ViewDrawer/ThreeDView.tsx', () => {
  // eslint-disable-next-line
  const React = require('react');
  return () => <div>3d building</div>;
});

jest.mock('archilyse-ui-components', () => {
  // eslint-disable-next-line
  const React = require('react');

  return {
    ...(jest.requireActual('archilyse-ui-components') as object),
    Heatmap: () => <div>Heatmap</div>,
  };
});

describe('SelectedView component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<SelectedView {...props} />);
  };

  beforeEach(() => {
    props = {
      view: C.VIEWS.TABLE,
      files: [],
      customFolders: [],
      data: [],
      site: MOCK_COMPLETED_SITE,
      tableProps: {},
      onClickFolder: jest.fn(),
      onClickCustomFolder: jest.fn(),
      isAdminDataReady: true,
      getEntityName: jest.fn(),
      filter: '',
      fileHandlers: {},
      widgetData: {},
      clientId: 1,
      uploadProps: {},
      loadingState: {},
    };
  });

  describe('Empty folder message', () => {
    beforeEach(() => {
      mockPathname = '/custom_folder';
    });
    it('renders <EmptyFolder /> when there are no files either folders', async () => {
      const { queryByTestId } = renderComponent();
      expect(queryByTestId('empty-data')).toBeInTheDocument();
    });
    it('does not render <EmptyFolder /> when there are files but no folders', async () => {
      props.files = [{ content_type: 'image/png' }];
      const { queryByTestId } = renderComponent();
      expect(queryByTestId('empty-data')).not.toBeInTheDocument();
    });
    it('does not render <EmptyFolder /> when there are folders but no files', async () => {
      props.customFolders = [{ type: 'custom-folder' }];
      const { queryByTestId } = renderComponent();
      expect(queryByTestId('empty-data')).not.toBeInTheDocument();
    });
    it('does not render <EmptyFolder /> when there are folders and files', async () => {
      props.customFolders = [{ type: 'custom-folder' }];
      props.files = [{ content_type: 'image/png' }];
      const { queryByTestId } = renderComponent();
      expect(queryByTestId('empty-data')).not.toBeInTheDocument();
    });
    it('it renders <EmptyFolder /> with a specific text when we are in an empty room', async () => {
      mockPathname = ROOM;
      renderComponent();
      expect(screen.getByText(/Empty Folder/)).toBeInTheDocument();
    });
  });

  describe('Filter files', () => {
    beforeEach(() => {
      mockPathname = '/custom_folder';
    });
    it('filters by name', async () => {
      const { queryByText } = renderComponent({ files: MOCK_FILES, filter: 'another' });
      expect(queryByText('plan1')).not.toBeInTheDocument();
      expect(queryByText('plan2')).not.toBeInTheDocument();
      expect(queryByText('sample_ifc')).not.toBeInTheDocument();
      expect(getByTextIngoringHidden('another_pdf')).toBeInTheDocument();
    });

    it('filters by label', async () => {
      const { queryByText } = renderComponent({ files: MOCK_FILES, filter: 'avocado' });
      expect(queryByText('plan1')).not.toBeInTheDocument();
      expect(queryByText('plan2')).not.toBeInTheDocument();
      expect(getByTextIngoringHidden('sample_ifc')).toBeInTheDocument();
      expect(queryByText('another_pdf')).not.toBeInTheDocument();
    });
  });

  // API currently returns same files for unit and for room, we filter those in the UI
  describe('Filter API files correctly in a unit and in a room', () => {
    const FILE_FROM_UNIT = {
      area_id: null,
      id: 17968,
      labels: [],
      name: 'wonderfulUnitFile.png',
      site_id: 1465,
      unit_id: 62558,
    };
    const FILE_FROM_ROOM = {
      area_id: 661017,
      id: 17969,
      name: 'payasoRoomFile.png',
      unit_id: 62558,
    };
    const MOCK_FILES_FROM_API = [FILE_FROM_UNIT, FILE_FROM_ROOM];

    it('Inside a unit, only unit files are shown', async () => {
      mockPathname = ROOMS;
      renderComponent({ files: MOCK_FILES_FROM_API, filter: '' });
      expect(screen.queryAllByText(new RegExp(FILE_FROM_UNIT.name)).length).toBeTruthy();
      expect(screen.queryAllByText(new RegExp(FILE_FROM_ROOM.name)).length).toBeFalsy();
    });

    it('Inside a room, only room files are shown', async () => {
      mockPathname = ROOM;
      renderComponent({ files: MOCK_FILES_FROM_API, filter: '' });
      expect(screen.queryAllByText(new RegExp(FILE_FROM_ROOM.name)).length).toBeTruthy();
      expect(screen.queryAllByText(new RegExp(FILE_FROM_UNIT.name)).length).toBeFalsy();
    });
  });

  describe('Filter data', () => {
    beforeEach(() => {
      mockPathname = '/sites';
    });
    it('filters a site entity by label', async () => {
      const { queryByText } = renderComponent({ files: MOCK_FILES, filter: 'papaya', data: MOCK_SITES });
      for (const file of MOCK_FILES) {
        expect(queryByText(file.name)).not.toBeInTheDocument();
      }
      expect(getByTextIngoringHidden(MOCK_SITES[0].name)).toBeInTheDocument();
    });
  });

  describe('Room folders', () => {
    const MOCK_ROOMS = [
      { area_type: 'KITCHEN', id: 1 },
      { area_type: 'ROOM', id: 2 },
    ];

    const MOCK_WIDGET_DATA = {
      areaData: {
        rooms: [
          { id: '1', netArea: 3.3400113016086705 },
          { id: '2', netArea: 13.243074758939072 },
        ],
      },
      buildingId: '2717',
      unitFloorplan: 'fake-link',
    };

    const roomProps = {
      data: MOCK_ROOMS,
      widgetData: MOCK_WIDGET_DATA,
      getEntityName: getRoomName,
    };

    beforeEach(() => {
      mockPathname = '/rooms';
    });

    it('are editable', async () => {
      renderComponent(roomProps);
      for (const room of MOCK_ROOMS) {
        const roomName = new RegExp(getRoomName(room));
        expect(getByTextIngoringHidden(roomName)).toBeInTheDocument();
      }
      const hasTags = screen.queryAllByTestId('tags-text-field').length > 0;
      expect(hasTags).toBeTruthy();
    });

    it('are clickable', async () => {
      const onClick = jest.fn();
      renderComponent({
        ...roomProps,
        onClickFolder: onClick,
      });
      for (const room of MOCK_ROOMS) {
        const roomName = new RegExp(getRoomName(room));
        fireEvent.click(getByTextIngoringHidden(roomName));
        expect(onClick).toHaveBeenCalled();
      }
    });

    it('do not have a context menu', async () => {
      renderComponent(roomProps);
      for (const room of MOCK_ROOMS) {
        const roomName = new RegExp(getRoomName(room));
        fireEvent.contextMenu(getByTextIngoringHidden(roomName));
        expect(screen.getByText('No contextual actions')).toBeInTheDocument();
      }
    });

    it('hovering over a room displays its net area in the pie chart', async () => {
      const expectedSurface = roomProps.widgetData.areaData.rooms[0].netArea.toFixed(1);
      renderComponent(roomProps);
      const roomName = new RegExp(getRoomName(MOCK_ROOMS[0]));
      const room = getByTextIngoringHidden(roomName);
      userEvent.hover(room);
      expect(screen.getByText(`${expectedSurface}m2`)).toBeInTheDocument();
      // react-testing-library does not unset internal store, so we have to explicitly hover out or the pie chart will still keep old value
      userEvent.unhover(room);
    });
  });

  describe('Context menu interaction', () => {
    beforeEach(() => {
      mockPathname = '/custom_folder';
    });

    it('shows a contextual menu in Empty Folder', async () => {
      renderComponent();
      fireEvent.contextMenu(screen.getByTestId('empty-data'));
      expect(screen.getByTestId('context-menu-action')).toBeInTheDocument();
    });

    it('shows a contextual menu in the Table', async () => {
      renderComponent({ view: C.VIEWS.TABLE, files: MOCK_FILES });
      fireEvent.contextMenu(screen.getByTestId('dms-table'));
      expect(screen.getByTestId('context-menu-action')).toBeInTheDocument();
    });

    it('shows a contextual menu in the Grid', async () => {
      renderComponent({ view: C.VIEWS.DIRECTORY, files: MOCK_FILES });
      fireEvent.contextMenu(screen.getByTestId('dms-grid'));
      expect(screen.getByTestId('context-menu-action')).toBeInTheDocument();
    });

    it('selects a file to cut', async () => {
      const { container } = renderComponent({ view: C.VIEWS.TABLE, files: MOCK_FILES });
      const fileName = MOCK_FILES[0].name;
      fireEvent.contextMenu(getByTextIngoringHidden(fileName));
      fireEvent.click(getByTextIngoringHidden('Cut'));
      expect(container.querySelector('.item-cut')).toBeInTheDocument();
    });

    it('selects a folder to cut', async () => {
      const { container } = renderComponent({ view: C.VIEWS.TABLE, customFolders: MOCK_FOLDERS });
      const folderName = MOCK_FOLDERS[0].name;

      fireEvent.contextMenu(getByTextIngoringHidden(folderName));
      fireEvent.click(getByTextIngoringHidden('Cut'));
      expect(container.querySelector('.item-cut')).toBeInTheDocument();
    });
  });

  describe('Loading message', () => {
    beforeEach(() => {
      mockPathname = '/sites';
    });

    it('Shows a loading message till the data arrives', async () => {
      const { rerender } = renderComponent({
        view: C.VIEWS.TABLE,
        data: [],
        loadingState: { entities: true, files: true, folders: true },
      });
      expect(screen.getByTestId('main-loading-indicator')).toBeInTheDocument();
      rerender(<SelectedView {...props} data={MOCK_SITES} loadingState={{}} />);
      expect(screen.queryByTestId('main-loading-indicator')).not.toBeInTheDocument();
      expect(screen.getByTestId('dms-table')).toBeInTheDocument();
    });
  });

  describe('Windowing behaviour', () => {
    beforeEach(() => {
      mockPathname = '/sites';
    });
    const MOCK_LARGE_PORTFOLIO = Array.from({ length: 100 }, (element, index) => {
      return {
        name: index < 50 ? 'siteA' : 'siteB',
        type: 'folder-sites',
        created: '2021-02-02',
        id: index,
        labels: [],
      };
    });

    const MOCK_SITES_WIDGET_DATA = {
      areaData: {
        sites: Array.from({ length: 100 }, (element, index) => ({ id: index, netArea: index < 50 ? 1 : 20 })),
      },
    };

    it('Renders only elements that are visible in the table', async () => {
      renderComponent({ view: C.VIEWS.TABLE, data: MOCK_LARGE_PORTFOLIO });
      fireEvent.click(screen.getByTestId('name'));
      // Only the first sites sorted ("siteB") should be rendered
      expect(screen.queryAllByText(/siteB/)).toBeTruthy();
      expect(screen.queryByText(/siteA/)).toBeFalsy();
    });

    it('Renders only elements that are visible in the grid', async () => {
      renderComponent({ view: C.VIEWS.DIRECTORY, data: MOCK_LARGE_PORTFOLIO });
      // No sorting, so siteA should be there by default
      expect(screen.queryAllByText(/siteA/)).toBeTruthy();
      expect(screen.queryByText(/siteB/)).toBeFalsy();
    });

    it('Widgets shows only the visible elemnts', async () => {
      renderComponent({
        view: C.VIEWS.TABLE,
        data: MOCK_LARGE_PORTFOLIO,
        widgetData: MOCK_SITES_WIDGET_DATA,
      });

      // Pie chart should have only the visible units on the screen, not all
      const totalNrOfUnits = MOCK_SITES_WIDGET_DATA.areaData.sites.reduce((accum, site) => site.netArea + accum, 0);
      const totalUnits = `${totalNrOfUnits} units`;
      const visibleUnits = screen.getByText(/units/).textContent;
      expect(visibleUnits).not.toEqual(totalUnits);

      // If we re-order, only siteB are shown and new visible items are loaded
      fireEvent.click(screen.getByTestId('name'));
      const newVisibleUnits = screen.getByText(/units/).textContent;
      expect(newVisibleUnits).not.toEqual(visibleUnits);
    });
  });

  describe('Widgets appeareance', () => {
    type TestCase = [DMSView];

    const TEST_CASES_WIDGET: TestCase[] = [[SITES], [BUILDINGS], [FLOORS], [UNITS], [ROOMS]];
    const TEST_CASES_NO_WIDGET: TestCase[] = [[CLIENTS], [CUSTOM_FOLDER], [TRASH], [ROOM]];

    it.each(TEST_CASES_WIDGET)('Does contain widgets in initial view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent({ data: MOCK_SITES });
      expect(screen.getAllByTestId('widget')).toBeTruthy();
    });

    it.each(TEST_CASES_NO_WIDGET)('Does not contain widgets in initial view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent({ data: MOCK_SITES });
      expect(screen.queryByTestId('widget')).toBeFalsy();
    });

    it.each(TEST_CASES_NO_WIDGET)(
      'Does not contain widgets after they have been loaded in a previous view: %s',
      async pathname => {
        mockPathname = SITES;

        const { rerender } = renderComponent();
        mockPathname = pathname;
        rerender(<SelectedView {...props} />);
        expect(screen.queryByTestId('widget')).toBeFalsy();
      }
    );
  });
});
