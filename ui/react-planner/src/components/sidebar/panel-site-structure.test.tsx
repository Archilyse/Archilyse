import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { SiteStructure } from '../../types';
import PanelSiteStructure from './panel-site-structure';

const MOCK_SITE_STRUCTURE: SiteStructure = {
  client_site_id: 'Leszku-payaso',
  site: {
    id: 1,
    name: 'Big-ass portfolio',
  },
  building: {
    id: 1,
    housenumber: '20-22',
    street: 'Technoparkstrasse',
  },
  floors: [
    {
      plan_id: 1,
      floor_number: 0,
    },
  ],
  planId: 1,
};

describe('PanelSiteStructure', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<PanelSiteStructure {...props} />);
  };

  beforeEach(() => {
    props = {
      siteStructure: {},
    };
  });

  it('Site structure is properly rendered', () => {
    renderComponent({
      siteStructure: MOCK_SITE_STRUCTURE,
    });
    expect(screen.queryByText(/Client site ID:/)).toBeInTheDocument();
    expect(screen.queryByText(/Site:/)).toBeInTheDocument();
    expect(screen.queryByText(/Building:/)).toBeInTheDocument();
    expect(screen.queryByText(/Floors:/)).toBeInTheDocument();
  });

  it('Site structure has appropriate links', () => {
    renderComponent({
      siteStructure: MOCK_SITE_STRUCTURE,
    });

    const ADMIN_URL = '/admin';
    const BUILDING_ID = MOCK_SITE_STRUCTURE.building.id;
    const siteURL = `${ADMIN_URL}/pipelines?site_id=${BUILDING_ID}`;
    const floorsURL = `${ADMIN_URL}/pipelines?site_id=${BUILDING_ID}`;
    const siteLinks = screen.getAllByRole('link');

    expect(siteLinks[0]).toHaveAttribute('href', siteURL);
    expect(siteLinks[1]).toHaveAttribute('href', floorsURL);
  });
});
