import * as React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { C } from 'Common/index';
import { SiteView } from '../../../src/components';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import { tabHeaders } from '.';

afterEach(cleanup);

const MOCKED_SITE = {
  lon: 8.05,
  lat: 47.39,
  basic_features_status: 'UNPROCESSED',
  client_id: 2,
  client_site_id: '1402401005',
  created: '2019-07-23T12:01:03.606043',
  currently_assigned: false,
  gcs_3d_model_link:
    'https://www.googleapis.com/download/storage/v1/b/archilyse-slam-pipeline/o/images%2F1402401005-3d.html?generation=1568969085226579&alt=media',
  gcs_buildings_link:
    'https://www.googleapis.com/download/storage/v1/b/archilyse-slam-pipeline/o/buildings%2F2646908.0_1249174.0.json?generation=1568645035795798&alt=media',
  gcs_json_surroundings_link:
    'https://www.googleapis.com/download/storage/v1/b/archilyse-slam-pipeline/o/surroundings%2F2646908.0_1249174.0.json?generation=1570711986188469&alt=media',
  id: 114,
  name: 'Aeschbachweg 12',
  pipeline_and_qa_complete: true,
  priority: 0,
  raw_dir: 'DigitizationPartnersultantsTest/',
  region: 'Aarau',
  results_completed: false,
  site_plan_file: '',
  updated: '2019-11-14T11:54:00.841656',
  validation_notes: null,
  ifc_import_status: 'SUCCESS',
  ifc_import_exceptions: {},
};

const MOCKED_FAILED_IFC_SITE = {
  ifc_import_status: 'FAILED',
  ifc_import_exceptions: { msg: "{'zipcode': ['Field may not be null.']}", code: 'DBValidationException' },
};

const QA_ROWS = 200;
const MOCKED_QA_ROW = [
  {
    ANF: 13.6,
    Obje: 1414,
    apartment_client_id: '1414.A.0.1',
    'building number': 'A',
    floor: 0,
    net_area: 78.5,
    number_of_rooms: 2.5,
    'unit number': 1,
  },
];

const MOCKED_CLIENT = {
  id: '1',
  name: 'Migros',
};

const MOCKED_QA = {
  id: 1,
  data: Array(QA_ROWS).fill(MOCKED_QA_ROW),
};

describe('Renders correctly', () => {
  beforeEach(() => MOCK_AUTHENTICATION());

  it('Trying to create a new site', () => {
    render(
      <MemoryRouter initialEntries={[`/site/new?client_id=${MOCKED_CLIENT.id}`]}>
        <SiteView site={{}} parent={MOCKED_CLIENT} />
      </MemoryRouter>
    );
    expect(screen.getByText(/New site/)).toBeInTheDocument();
  });

  it('While trying to edit a site with no qa data', () => {
    render(
      <MemoryRouter>
        <SiteView site={MOCKED_SITE} />
      </MemoryRouter>
    );
    expect(screen.getByText(new RegExp(MOCKED_SITE.name))).toBeInTheDocument();
  });

  it('While trying to edit a site with qa data', () => {
    render(
      <MemoryRouter>
        <SiteView site={MOCKED_SITE} qa={MOCKED_QA} isUpdated={true} />
      </MemoryRouter>
    );
    expect(screen.getByText(new RegExp(MOCKED_SITE.name))).toBeInTheDocument();
  });
});

describe('ifc status tests', () => {
  beforeEach(() => MOCK_AUTHENTICATION());

  it('should render message that site has not been simulated with ifc', async () => {
    const { container, getByTestId } = render(
      <MemoryRouter>
        <SiteView site={[]} />
      </MemoryRouter>
    );
    fireEvent.click(getByTestId('ifc-status-tab'));
    await waitFor(() => container.querySelector('.ifc-status-container'));
    expect(screen.getByText(/IFC file has not been added to this site/)).toBeInTheDocument();
  });

  it('should render message that there was a failure', async () => {
    const { container, getByTestId } = render(
      <MemoryRouter>
        <SiteView site={MOCKED_FAILED_IFC_SITE} />
      </MemoryRouter>
    );
    fireEvent.click(getByTestId('ifc-status-tab'));
    await waitFor(() => container.querySelector('.ifc-status-container'));
    expect(screen.getByText(/\{'zipcode': \['Field may not be null\.'\]\}/)).toBeInTheDocument();
    // expect (screen.getByText(/Field may not be null/)).toBeInTheDocument()
  });

  it('should render message that site has been simulated successfully', async () => {
    const { container, getByTestId } = render(
      <MemoryRouter>
        <SiteView site={MOCKED_SITE} />
      </MemoryRouter>
    );
    fireEvent.click(getByTestId('ifc-status-tab'));
    await waitFor(() => container.querySelector('.ifc-status-container'));
    expect(screen.getByText(/SUCCESS/)).toBeInTheDocument();
  });
});

describe('Tabs visibility', () => {
  it(`As an ${C.ROLES.ADMIN}, I can see all tabs`, () => {
    MOCK_AUTHENTICATION(C.ROLES.ADMIN);
    render(
      <MemoryRouter>
        <SiteView site={MOCKED_SITE} />
      </MemoryRouter>
    );
    tabHeaders.forEach(header => {
      expect(screen.getByText(header)).toBeInTheDocument();
    });
  });

  it(`As a ${C.ROLES.TEAMMEMBER}, I only see General & QA tab`, () => {
    MOCK_AUTHENTICATION(C.ROLES.TEAMMEMBER);
    const GENERAL_TAB = 'General';
    const QA_TAB = 'QA';

    render(
      <MemoryRouter>
        <SiteView site={MOCKED_SITE} />
      </MemoryRouter>
    );
    // It should see General & QA
    expect(screen.getByText(GENERAL_TAB)).toBeInTheDocument();
    expect(screen.getByText(QA_TAB)).toBeInTheDocument();
    // It should not see the other tabs
    tabHeaders
      .filter(header => ![QA_TAB, GENERAL_TAB].includes(header))
      .forEach(header => {
        expect(screen.queryByText(header)).not.toBeInTheDocument();
      });
  });
});
