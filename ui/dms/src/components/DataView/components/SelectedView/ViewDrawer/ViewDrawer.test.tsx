import React from 'react';
import { render, screen } from '@testing-library/react';
import { C } from 'Common';
import { WIDGETS_TABS } from '../widgets';
import DetailsDrawer from './index';

const { SITES, CLIENTS, BUILDINGS, FLOORS, UNITS, ROOMS, CUSTOM_FOLDER, TRASH } = C.DMS_VIEWS;
type DMSView = typeof C.DMS_VIEWS[keyof typeof C.DMS_VIEWS];
type TestCase = [DMSView];

let mockPathname;
jest.mock('../../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
  usePrevious: () => {},
}));

describe('View drawer component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<DetailsDrawer {...props} />);
  };
  beforeEach(() => {
    props = {
      buildingId: null, // If we put a fake id here there will be a WebGL error because the component tries to display incorrect 3d data
      unitFloorplan: 'http://some-fake-link.com/some_fake_image.jpg',
    };
  });

  describe('Map tab', () => {
    const HAS_MAP_TAB: TestCase[] = [[SITES], [BUILDINGS]];
    const DOES_NOT_HAVE_MAP_TAB: TestCase[] = [[CLIENTS], [CUSTOM_FOLDER], [TRASH], [FLOORS], [UNITS], [ROOMS]];

    it.each(HAS_MAP_TAB)('is visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent(props);
      expect(screen.getByText(WIDGETS_TABS.MAP)).toBeInTheDocument();
    });
    it.each(DOES_NOT_HAVE_MAP_TAB)('is not visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent({ props });
      expect(screen.queryByText(WIDGETS_TABS.MAP)).not.toBeInTheDocument();
    });
  });

  describe('3d tab', () => {
    const HAS_3D_TAB: TestCase[] = [[FLOORS], [UNITS], [ROOMS]];
    const DOES_NOT_HAVE_3D_TAB: TestCase[] = [[CLIENTS], [CUSTOM_FOLDER], [SITES], [BUILDINGS], [TRASH]];

    it.each(HAS_3D_TAB)('is visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent(props);
      expect(screen.getByText(WIDGETS_TABS.THREE_D)).toBeInTheDocument();
    });

    it.each(DOES_NOT_HAVE_3D_TAB)('is not visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent({ props });
      expect(screen.queryByText(WIDGETS_TABS.THREE_D)).not.toBeInTheDocument();
    });
  });

  describe('Unit tab', () => {
    const HAS_FLOORPLAN_TAB: TestCase[] = [[ROOMS]];
    const DOES_NOT_HAVE_FLOORPLAN_TAB: TestCase[] = [[FLOORS], [UNITS], [CUSTOM_FOLDER], [SITES], [BUILDINGS], [TRASH]];

    it.each(HAS_FLOORPLAN_TAB)('is visible in view along 3d view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent(props);
      expect(screen.getByText(WIDGETS_TABS.FLOORPLAN)).toBeInTheDocument();
      expect(screen.getByText(WIDGETS_TABS.THREE_D)).toBeInTheDocument();
    });

    it.each(DOES_NOT_HAVE_FLOORPLAN_TAB)('is not visible in view: %s', async pathname => {
      mockPathname = pathname;
      renderComponent({ props });
      expect(screen.queryByText(WIDGETS_TABS.FLOORPLAN)).not.toBeInTheDocument();
    });
  });
});
