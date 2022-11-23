import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { C } from 'Common';
import { capitalize } from 'archilyse-ui-components';
import Permissions from './index';

// @TODO: Cases for receiving initial permissions and erasing a permission

const SAVE = 'Save';

const mockPathname = '/profile';
jest.mock('../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
}));

const MOCK_SITES = [
  { name: 'A nice site', id: 1 },
  { name: 'Wonderful choso', id: 2 },
  { name: 'Technoparkstrasse', id: 3 },
  { name: 'El chosaso', id: 4 },
];

const parsePermissionText = permission => capitalize(permission.toLowerCase().replace('_', ' '));

const MOCK_USERS = [{ id: 1, name: 'John', roles: ['DMS'], login: 'john' }];
const { READ, EDIT, READ_ALL, EDIT_ALL } = C.DMS_PERMISSIONS;
const [READ_TEXT, EDIT_TEXT, ALL_TEXT] = Object.keys(C.DMS_PERMISSIONS).map(parsePermissionText);

describe('Permissions component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<Permissions {...props} />);
  };
  beforeEach(() => {
    props = {
      users: MOCK_USERS,
      sites: MOCK_SITES,
      permissions: [],
    };
  });

  const assertRuleFormIsShown = () => {
    expect(screen.getByText('Add permissions')).toBeInTheDocument();
    expect(screen.getByText('Permission')).toBeInTheDocument();
    expect(screen.getByText('Sites')).toBeInTheDocument();
  };

  it('renders a message when there are no users', async () => {
    renderComponent({ users: [] });
    expect(screen.getByText('There are no users created yet.')).toBeInTheDocument();
  });

  it('does not render a message when there are no users', async () => {
    renderComponent();
    expect(screen.queryByText('There are no users created yet.')).toBeFalsy();
  });

  it(`Add the "${READ}" permission on a site for a given user`, async () => {
    renderComponent();
    fireEvent.click(screen.getByText('Add permission'));
    assertRuleFormIsShown();

    // Select "Read" permissions
    const listOfButtons = screen.getAllByRole('button');
    const permissionsDropdown = listOfButtons[1];
    fireEvent.mouseDown(permissionsDropdown);
    fireEvent.click(screen.getByText(READ_TEXT));

    // Select a site and add the rule
    const SELECTED_SITE = MOCK_SITES[0];
    fireEvent.mouseDown(screen.getByTestId('tags-text-field'));
    fireEvent.click(screen.getByText(SELECTED_SITE.name));
    fireEvent.click(screen.getByText(SAVE));

    // The rule should be added
    const EXPECTED_RULE = `${READ_TEXT.toLowerCase()}:${SELECTED_SITE.name}`;
    expect(screen.getByText(EXPECTED_RULE)).toBeInTheDocument();
  });

  it(`Add the "${EDIT}" permission on a site for a given user`, async () => {
    renderComponent();
    fireEvent.click(screen.getByText('Add permission'));
    assertRuleFormIsShown();

    // Select "Edit" permission
    const listOfButtons = screen.getAllByRole('button');
    const permissionsDropdown = listOfButtons[1];
    fireEvent.mouseDown(permissionsDropdown);
    fireEvent.click(screen.getByText(EDIT_TEXT));

    // Select several sites
    const SELECTED_SITES = [MOCK_SITES[0], MOCK_SITES[1], MOCK_SITES[2]];

    for (const site of SELECTED_SITES) {
      fireEvent.mouseDown(screen.getByTestId('tags-text-field'));
      fireEvent.click(screen.getByText(site.name));
    }
    fireEvent.click(screen.getByText(SAVE));

    // The rule should be added
    const EXPECTED_SITE_STRING = SELECTED_SITES.map(site => site.name).join(',');
    const EXPECTED_RULE = `${EDIT_TEXT.toLowerCase()}:${EXPECTED_SITE_STRING}`;
    expect(screen.getByText(EXPECTED_RULE)).toBeInTheDocument();
  });

  it(`Add the "${READ_ALL}" permission for a given user`, async () => {
    renderComponent();
    fireEvent.click(screen.getByText('Add permission'));
    assertRuleFormIsShown();

    // Select "Read all" permission
    const listOfButtons = screen.getAllByRole('button');
    const permissionsDropdown = listOfButtons[1];
    fireEvent.mouseDown(permissionsDropdown);
    fireEvent.click(screen.getByText(ALL_TEXT));
    fireEvent.click(screen.getByText(SAVE));

    // The rule should be added
    const EXPECTED_RULE = parsePermissionText(READ_ALL);
    expect(screen.getByText(EXPECTED_RULE)).toBeInTheDocument();
  });

  it(`Add the "${EDIT_ALL}" permission for a given user`, async () => {
    renderComponent();
    fireEvent.click(screen.getByText('Add permission'));
    assertRuleFormIsShown();

    // Select "Edit all" permission
    const listOfButtons = screen.getAllByRole('button');
    const permissionsDropdown = listOfButtons[1];
    fireEvent.mouseDown(permissionsDropdown);
    fireEvent.click(screen.getByText('Edit all'));

    fireEvent.click(screen.getByText(SAVE));

    // The rule should be added
    const EXPECTED_RULE = 'WRITE ALL';
    expect(screen.getByText(EXPECTED_RULE)).toBeInTheDocument();
  });
});
