import * as React from 'react';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../../../../tests/utils';
import BuildingPipelines from './BuildingPipelines';

const MOCK_BUILDING = {
  city: 'Zürich',
  client_building_id: '10002',
  created: '2021-08-24T12:27:14.373130',
  elevation: 424.829315185547,
  elevation_override: null,
  housenumber: '1',
  id: 4481,
  labels: null,
  site_id: 3004,
  street: 'Cordelia-Guggenheim-Weg',
  triangles_gcs_link: '',
  updated: '2021-09-06T07:51:24.513252',
  zipcode: '8050',
};
const MOCK_PIPELINES = [
  {
    building_housenumber: '1',
    building_id: 4481,
    classified: true,
    client_building_id: '10002',
    client_site_id: '10002',
    created: '2021-08-24T12:29:12.385337',
    floor_numbers: [1],
    georeferenced: true,
    id: 12648,
    is_masterplan: false,
    labelled: true,
    splitted: true,
    units_linked: true,
    updated: '2022-01-31T11:19:26.873901',
  },
  {
    building_housenumber: '1',
    building_id: 4481,
    classified: true,
    client_building_id: '10002',
    client_site_id: '10002',
    created: '2021-08-24T12:29:44.606294',
    floor_numbers: [2, 3, 4, 5],
    georeferenced: true,
    id: 12649,
    is_masterplan: false,
    labelled: true,
    splitted: true,
    units_linked: true,
    updated: '2022-01-31T11:19:20.148070',
  },
  {
    building_housenumber: '1',
    building_id: 4481,
    classified: true,
    client_building_id: '10002',
    client_site_id: '10002',
    created: '2021-08-24T12:32:37.594732',
    floor_numbers: [6],
    georeferenced: true,
    id: 12650,
    is_masterplan: false,
    labelled: true,
    splitted: true,
    units_linked: true,
    updated: '2022-01-31T11:19:30.372233',
  },
  {
    building_housenumber: '1',
    building_id: 4481,
    classified: true,
    client_building_id: '10002',
    client_site_id: '10002',
    created: '2021-08-24T12:33:27.700221',
    floor_numbers: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
    georeferenced: true,
    id: 12651,
    is_masterplan: false,
    labelled: true,
    splitted: true,
    units_linked: true,
    updated: '2022-01-31T11:19:35.036475',
  },
  {
    building_housenumber: '1',
    building_id: 4481,
    classified: true,
    client_building_id: '10002',
    client_site_id: '10002',
    created: '2021-08-24T12:34:22.508447',
    floor_numbers: [23, 25],
    georeferenced: true,
    id: 12652,
    is_masterplan: false,
    labelled: true,
    splitted: true,
    units_linked: true,
    updated: '2022-01-31T11:19:08.057501',
  },
  {
    building_housenumber: '1',
    building_id: 4481,
    classified: true,
    client_building_id: '10002',
    client_site_id: '10002',
    created: '2021-08-24T12:41:48.796768',
    floor_numbers: [24, 26],
    georeferenced: true,
    id: 12655,
    is_masterplan: false,
    labelled: true,
    splitted: true,
    units_linked: true,
    updated: '2022-01-31T11:19:12.778027',
  },
];

describe('BuildingPipelines component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    const route = '/pipelines?site_id=1455';
    return renderWithRouter(<BuildingPipelines {...props} />, route);
  };

  beforeEach(async () => {
    props = {
      pipelines: [],
      building: {},
      reloadPipelines: () => {},
    };
  });

  describe('Render a row per plan of the building', () => {
    it('Renders one row per pipeline', () => {
      renderComponent({ pipelines: MOCK_PIPELINES, building: MOCK_BUILDING, reloadPipelines: jest.fn() });

      MOCK_PIPELINES.forEach(pipeline => {
        expect(screen.getByText(`Plan ${pipeline.id}`)).toBeInTheDocument();
      });
    });
  });

  describe('Masterplan interaction', () => {
    it('Shows the masterplan row and can change it', () => {
      const pipelines = [...MOCK_PIPELINES];
      pipelines[0].is_masterplan = true;
      renderComponent({ pipelines: pipelines, building: MOCK_BUILDING });

      // Masterplan will be checked and the rest unchecked
      const checkedRadioButtons = screen.getAllByRole('radio', { checked: true });
      const uncheckedRadioButtons = screen.getAllByRole('radio', { checked: false });
      expect(checkedRadioButtons).toHaveLength(1);
      expect(uncheckedRadioButtons).toHaveLength(pipelines.length - 1);

      // If we select a different masterplan, the UI updates it
      const newMasterPlanRow = uncheckedRadioButtons[0].closest('tr');
      userEvent.click(uncheckedRadioButtons[0]);
      expect(within(newMasterPlanRow).getByRole('radio', { checked: true }));
    });
  });
});
