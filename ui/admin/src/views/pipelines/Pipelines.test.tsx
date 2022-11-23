import * as React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../../../tests/utils';
import MOCK_BUILDINGS_BY_SITE from '../../../__mocks__/entities/buildings_by_site';

import Pipelines, { BUILDING_STATUS } from './Pipelines';

describe('Pipeline component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    const MOCK_ROUTE = '/pipelines?site_id=1455';
    return renderWithRouter(<Pipelines {...props} />, MOCK_ROUTE);
  };

  beforeEach(async () => {
    renderComponent();
    await waitFor(() => expect(screen.queryByText('Building')).toBeInTheDocument());
  });

  it('Renders correctly the buildings of the site', async () => {
    MOCK_BUILDINGS_BY_SITE.forEach(building => {
      expect(screen.getByText(`Building: ${building.client_building_id || ''}`, { exact: false })).toBeInTheDocument();
    });
  });

  it('Clicking on a building name expand its contents', () => {
    const [building] = MOCK_BUILDINGS_BY_SITE;

    // Everything collapsed by default
    let buildingPipelineHeaders = screen.queryAllByText('Labelled');
    buildingPipelineHeaders.forEach(header => {
      expect(header).not.toBeVisible();
    });

    // If we click on a building name
    const firstBuilding = screen.queryAllByText(`Building: ${building.client_building_id}`, { exact: false })[0];
    userEvent.click(firstBuilding);

    // Its pipelines are expanded
    buildingPipelineHeaders = screen.queryAllByText('Labelled');
    buildingPipelineHeaders.forEach(header => {
      waitFor(() => expect(header).toBeVisible());
    });
  });

  it('Shows an "Edit" dialog on clicking in the edit column of a building', async () => {
    const EDIT_ICONS = screen.getAllByTestId('edit-building-button');
    expect(EDIT_ICONS.length).toBe(MOCK_BUILDINGS_BY_SITE.length);

    // If we click on icon
    userEvent.click(EDIT_ICONS[0]);

    // A dialog is rendered with two buttons
    expect(screen.getAllByText('Save').length > 0).toBeTruthy();
    expect(screen.getAllByText('Delete').length > 0).toBeTruthy();

    EDIT_ICONS.forEach((icon, index) => {
      // If we click on icon
      userEvent.click(icon);

      // A dialog is rendered with two buttons
      expect(screen.getAllByText('Save').length > 0).toBeTruthy();
      expect(screen.getAllByText('Delete').length > 0).toBeTruthy();
      // And we are sure we are editing the right building
      expect(
        screen.getByText(`Editing building: ${MOCK_BUILDINGS_BY_SITE[index].id}`, { exact: false })
      ).toBeInTheDocument();
    });
  });

  it('Shows an "Add" dialog on clicking in the edit column of a building', async () => {
    // If we click on Add icon
    userEvent.click(screen.getAllByTestId('add-building-button')[0]);

    // A dialog is rendered with a button to create the building
    expect(screen.getAllByText('Create').length > 0).toBeTruthy();
  });

  it('Shows properly the building status depending on its pipelines', () => {
    // As per the mock data (pipelines_by_site.js) there should be: 1 COMPLETED & 1  IN_PROGRESS & 1 NOT_STARTED
    expect(screen.getByText(BUILDING_STATUS.COMPLETED, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(BUILDING_STATUS.IN_PROGRESS, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(BUILDING_STATUS.NOT_STARTED, { exact: false })).toBeInTheDocument();
  });

  it('Pipeline links are only shown after selecting a masterplan', () => {
    // Initially there is no masterplan, no links on the table to go the pipeline
    const buildingTable = () => screen.getByTestId('building-list');
    expect(within(buildingTable()).queryByRole('link')).not.toBeInTheDocument();

    // If we expand a building and select a masterplan
    const firstBuilding = screen.queryAllByText(`Building: `, { exact: false })[0];
    userEvent.click(firstBuilding);
    userEvent.click(screen.getAllByRole('radio')[0]);

    // We will see links to advance to the pipeline
    expect(within(buildingTable()).getAllByRole('link').length).toBeGreaterThan(0);
  });
});
