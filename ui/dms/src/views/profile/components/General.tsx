import React, { useContext } from 'react';
import { auth, Form, Icon, SnackbarContext } from 'archilyse-ui-components';
import { C } from '../../../common';
import { UserModel } from '../../../common/types';
import fields from '../../../common/forms/userProfile';
import { ProviderRequest } from '../../../providers';
import './general.scss';

const CLOSE_ICON_COLOR = '#434C50';

const getValue = (user: UserModel) => {
  return {
    name: user?.name || '',
    roles: user?.roles.join(', ') || '',
    email: user.email || '',
  };
};

const getRequestValues = values => ({
  email: values.email,
  ...(values.password ? { password: values.password } : {}),
});

const General = ({ user, mutate, onCancel }) => {
  const { id } = auth.getUserInfo();

  const snackbar = useContext(SnackbarContext);

  const handleSubmit = async values => {
    await ProviderRequest.put(C.ENDPOINTS.USER(id), getRequestValues(values));
    mutate();
    snackbar.show({ message: 'Saved successfully', severity: 'success' });
  };

  if (!user) return null;

  return (
    <div className="general-profile-container">
      <div className="general-profile-header">
        <h3 className="general-profile-title">Edit profile</h3>
        <button className="close-button" onClick={() => onCancel(false)}>
          <Icon style={{ marginLeft: '0', fontSize: '24px', color: CLOSE_ICON_COLOR }}>close</Icon>
        </button>
      </div>

      <>
        <h4>General information</h4>
        <div className="user-profile-container">
          <Form
            separatedLabels
            fields={fields}
            submitButtonId={'save_profile'}
            showCancelButton={true}
            onCancel={onCancel}
            value={getValue(user)}
            onSubmit={handleSubmit}
            watch={['password']}
          />
        </div>
      </>
    </div>
  );
};

export default General;
