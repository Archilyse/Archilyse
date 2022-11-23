import React from 'react';
import { render, screen } from '@testing-library/react';
import { C } from 'Common';
import { OpenedFile } from 'Common/types';
import { WIDGETS_TABS } from '../widgets';
import DetailsDrawer from './index';

const MOCK_FILE_DETAILS: OpenedFile = {
  name: 'plan1',
  type: C.MIME_TYPES.JPEG,
  labels: [],
  id: 1,
  size: 1232,
  created: '2019-02-02',
  updated: '2019-02-02',
  comments: [],
};

const { SITES, CLIENTS, BUILDINGS, FLOORS, UNITS, ROOMS, CUSTOM_FOLDER, TRASH } = C.DMS_VIEWS;
type DMSView = typeof C.DMS_VIEWS[keyof typeof C.DMS_VIEWS];

let mockPathname;
jest.mock('../../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
  usePrevious: () => {},
}));

const MOCK_AREA_DATA = {
  floors: [
    { id: '12522', netArea: 390.84278479898046, name: 'Floor 0' },
    { id: '12523', netArea: 601.1704691159182, name: 'Floor 1' },
    { id: '12524', netArea: 604.9551220302199, name: 'Floor 2' },
    { id: '12525', netArea: 608.2619054347667, name: 'Floor 3' },
    { id: '12526', netArea: 605.6258426751153, name: 'Floor 4' },
  ],
};

describe('Details drawer component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<DetailsDrawer {...props} />);
  };
  beforeEach(() => {
    props = {
      details: undefined,
      areaData: MOCK_AREA_DATA,
      onHoverPieChartItem: () => {},
      onChange: () => {},
      onRenameFile: () => {},
      onDownload: () => {},
      onAddComment: () => {},
      onDelete: () => {},
    };
  });

  type TestCase = [DMSView];
  const HAS_ANALYSIS_TAB: TestCase[] = [[SITES], [BUILDINGS], [FLOORS], [UNITS], [ROOMS]];
  const DOES_NOT_HAVE_ANALYTIS_TAB: TestCase[] = [[CLIENTS], [CUSTOM_FOLDER], [TRASH]];

  describe('Analysis tab', () => {
    it.each(HAS_ANALYSIS_TAB)('is visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent(props);
      expect(screen.getByText(WIDGETS_TABS.DASHBOARD)).toBeInTheDocument();
    });
    it.each(DOES_NOT_HAVE_ANALYTIS_TAB)('is not visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent(props);
      expect(screen.queryByText(WIDGETS_TABS.DASHBOARD)).not.toBeInTheDocument();
    });
  });

  describe('Details tab', () => {
    it('Is visible if we open a file', () => {
      renderComponent({ details: MOCK_FILE_DETAILS });
      expect(screen.getByText(WIDGETS_TABS.DETAILS)).toBeInTheDocument();
      expect(screen.getByText(WIDGETS_TABS.COMMENTS)).toBeInTheDocument();
    });

    it('Is not visible without a file', () => {
      renderComponent({ details: undefined });
      expect(screen.queryByText(WIDGETS_TABS.DETAILS)).not.toBeInTheDocument();
      expect(screen.queryByText(WIDGETS_TABS.COMMENTS)).not.toBeInTheDocument();
    });

    it.each(HAS_ANALYSIS_TAB)('is visible with analysis tab: %s', async pathname => {
      mockPathname = pathname;
      renderComponent({ details: MOCK_FILE_DETAILS });
      expect(screen.queryByText(WIDGETS_TABS.DASHBOARD)).toBeInTheDocument();
      expect(screen.queryByText(WIDGETS_TABS.DETAILS)).toBeInTheDocument();
      expect(screen.queryByText(WIDGETS_TABS.COMMENTS)).toBeInTheDocument();
    });
  });
});
