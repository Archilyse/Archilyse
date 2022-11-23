import React from 'react';
import { render, screen } from '@testing-library/react';
import { C } from 'Common';
import userEvent from '@testing-library/user-event';
import * as commonHooks from 'Components/DataView/hooks';
import ThreeDView from './ThreeDView';

const mockPathname = C.DMS_VIEWS.SITES;
jest.mock('../../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
  usePrevious: () => {},
}));

const SIMULATION_MODE = {
  THREE_D_VECTOR: 'THREE_D_VECTOR',
  DASHBOARD: 'DASHBOARD',
};

// Mocked the whole module in order to easily mock <SimulationViewer />
jest.mock('archilyse-ui-components', () => {
  // eslint-disable-next-line
  const React = require('react'); // https://github.com/facebook/jest/issues/2567
  return {
    SIMULATION_MODE,
    LoadingIndicator: () => <div role="alert"></div>,
    SimulationViewer: ({ buildingId, simType }) => (
      <div data-testid="simulation-viewer">
        Building ID to load {buildingId} with simType: {simType}
      </div>
    ),
  };
});

describe('ThreedView component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<ThreeDView {...props} />);
  };
  beforeEach(() => {
    props = {
      buildingId: 1,
      showToggles: true,
    };
  });

  it('Shows only a loading indicator with no building id', () => {
    renderComponent({ buildingId: null });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.queryByTestId('simulation-viewer')).not.toBeInTheDocument();
  });

  describe('Toggles', () => {
    const MOCK_CURRENT_UNITS_WITHOUT_PH_PRICE = [{ unit_client_id: 1 }, { unit_client_id: 1 }];
    const MOCK_CURRENT_UNITS_WITH_PH_PRICE = [
      { unit_client_id: 1, ph_final_gross_rent_annual_m2: 10 },
      { unit_client_id: 1, ph_final_gross_rent_annual_m2: 50 },
    ];

    it('Does not show any toggle with `showToggles === false`', () => {
      renderComponent({ showToggles: false });
      expect(screen.queryByText('Map')).not.toBeInTheDocument();
      expect(screen.queryByText('Price dimension')).not.toBeInTheDocument();
    });

    it('Shows "map" toggle with `showToggles === true`', () => {
      renderComponent({ showToggles: true });
      expect(screen.queryByText('Map')).toBeInTheDocument();
    });

    it('Does not show "Price dimension" toggle with current units without price', () => {
      jest
        .spyOn(commonHooks, 'useStore')
        .mockImplementation(fn => fn({ currentUnits: MOCK_CURRENT_UNITS_WITHOUT_PH_PRICE } as any));

      renderComponent({ showToggles: true });
      expect(screen.queryByText('Price dimension')).not.toBeInTheDocument();
    });

    it('With current units with price: Shows map toggle & price toggle', () => {
      jest
        .spyOn(commonHooks, 'useStore')
        .mockImplementation(fn => fn({ currentUnits: MOCK_CURRENT_UNITS_WITH_PH_PRICE } as any));
      renderComponent({ showToggles: true });
      expect(screen.queryByText('Price dimension')).toBeInTheDocument();
    });
  });

  it('Clicking on map toggle changes the background', () => {
    renderComponent();
    expect(screen.getByText(new RegExp(SIMULATION_MODE.THREE_D_VECTOR))).toBeInTheDocument();
    userEvent.click(screen.getByText('Map'));
    expect(screen.getByText(new RegExp(SIMULATION_MODE.DASHBOARD))).toBeInTheDocument();
  });
});
