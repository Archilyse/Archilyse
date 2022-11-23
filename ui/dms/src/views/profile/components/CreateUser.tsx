import React, { useContext } from 'react';
import { auth, Form, Icon, SnackbarContext } from 'archilyse-ui-components';
import { C } from '../../../common';
import fields from '../../../common/forms/createUser';
import { ProviderRequest } from '../../../providers';
import './createUser.scss';

const { ROLES } = C;

const ROLE_LABELS = {
  [ROLES.ARCHILYSE_ONE_ADMIN]: 'Admin',
  [ROLES.DMS_LIMITED]: 'User',
};

const parseFields = (formFields, roles = []) =>
  formFields.map(field => {
    if (field.name === 'roles') {
      field.options = (roles || []).map(role => ({ label: ROLE_LABELS[role], value: role }));
    }
    return field;
  });

const getClientId = () => {
  const { client_id } = auth.getUserInfo();

  return client_id;
};

const getRequestValues = (values, clientId) => ({
  ...values,
  roles: [values.roles],
  client_id: clientId,
});

const roles = [C.ROLES.ARCHILYSE_ONE_ADMIN, C.ROLES.DMS_LIMITED];

const CreateUser = ({ onCreateUser, onCancel }) => {
  const snackbar = useContext(SnackbarContext);

  const handleSubmit = async values => {
    const { repeated_password, ...otherValues } = values;
    await ProviderRequest.post(C.ENDPOINTS.USER(), getRequestValues(otherValues, getClientId()));
    onCreateUser();
    snackbar.show({ message: 'Saved successfully', severity: 'success' });
  };

  const parsedFields = parseFields(fields, roles);

  return (
    <div className="create-user-container">
      <div className="create-user-header">
        <h3 className="create-user-title">Create user</h3>
        <button className="close-button" onClick={() => onCancel(false)}>
          <Icon style={{ marginLeft: '0', fontSize: '24px' }}>close</Icon>
        </button>
      </div>

      <>
        <h4>General information</h4>
        <div className="user-profile-container">
          <Form
            id={'create-user-form'}
            submitButtonId={'save-dms-user'}
            showCancelButton={true}
            onCancel={onCancel}
            fields={parsedFields}
            onSubmit={handleSubmit}
            separatedLabels
          />
        </div>
      </>
    </div>
  );
};

export default CreateUser;
