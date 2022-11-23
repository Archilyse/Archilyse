import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import { C } from 'Common';
import { capitalize } from 'archilyse-ui-components';

import RuleForm from './RuleForm';

const { READ_ALL, EDIT_ALL } = C.DMS_PERMISSIONS;

const parsePermissionText = permission => capitalize(permission.toLowerCase().replace('_', ' '));
const MOCK_SITES = [
  { name: 'A nice site', id: 1 },
  { name: 'Wonderful choso', id: 2 },
  { name: 'Technoparkstrasse', id: 3 },
  { name: 'El chosaso', id: 4 },
];

describe('RuleForm component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<RuleForm {...props} />);
  };

  beforeEach(() => {
    props = {
      onSubmit: () => {},
      suggestedSites: MOCK_SITES,
      onClose: () => {},
    };
  });

  it('Show the list of sites as options', async () => {
    const { getByTestId, getByText } = renderComponent();
    fireEvent.mouseDown(getByTestId('tags-text-field'));
    for (const site of MOCK_SITES) {
      expect(getByText(site.name)).toBeInTheDocument();
    }
  });

  it('Show the list of permissions as options', async () => {
    const { getByText, queryAllByRole } = renderComponent();
    const [permissionsDropdown] = queryAllByRole('button');
    fireEvent.mouseDown(permissionsDropdown);
    for (const permission of Object.keys(C.DMS_PERMISSIONS)) {
      const PERMISSION_TEXT = parsePermissionText(permission);
      expect(getByText(PERMISSION_TEXT)).toBeInTheDocument();
    }
  });

  it(`On select "${READ_ALL}" permission, no sites can be selected`, async () => {
    const { getByText, queryAllByRole, queryByTestId } = renderComponent();

    const ALL_TEXT = parsePermissionText(READ_ALL);
    const [permissionsDropdown] = queryAllByRole('button');
    fireEvent.mouseDown(permissionsDropdown);
    fireEvent.click(getByText(ALL_TEXT));

    expect(queryByTestId('tags-text-field')).not.toBeInTheDocument();
    expect(getByText('This will give the user read permissions in every site')).toBeInTheDocument();
  });

  it(`On select "${EDIT_ALL}" permission, no sites can be selected`, async () => {
    const { getByText, queryAllByRole, queryByTestId } = renderComponent();

    const ALL_TEXT = 'Edit all';
    const [permissionsDropdown] = queryAllByRole('button');
    fireEvent.mouseDown(permissionsDropdown);
    fireEvent.click(getByText(ALL_TEXT));

    expect(queryByTestId('tags-text-field')).not.toBeInTheDocument();
    expect(getByText('This will give the user edit permissions in every site')).toBeInTheDocument();
  });

  it('Display an error when creating a rule without permissions or sites', async () => {
    const { getByText } = renderComponent();
    fireEvent.click(getByText('Save'));
    expect(getByText('Please add a permission')).toBeInTheDocument();
    expect(getByText('Please add at least one site')).toBeInTheDocument();
  });

  it('Permission/Edit user drawer can be closed', async () => {
    const onClose = jest.fn();
    const { getByTestId } = renderComponent({ onClose });
    fireEvent.click(getByTestId('close-button'));
    expect(onClose).toHaveBeenCalled();
  });
});
