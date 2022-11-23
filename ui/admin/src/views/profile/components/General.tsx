import React, { useContext } from 'react';
import useSWR from 'swr';
import { auth, Form, SnackbarContext } from 'archilyse-ui-components';
import { C } from '../../../common';
import { UserModel } from '../../../common/types';
import fields from '../../../common/forms/userProfile';
import { ProviderRequest } from '../../../providers';
import './general.scss';

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

const General = () => {
  const { id } = auth.getUserInfo();
  const { data: user, mutate } = useSWR<UserModel>(C.ENDPOINTS.USER(id), ProviderRequest.get);

  const snackabr = useContext(SnackbarContext);

  const handleSubmit = async values => {
    await ProviderRequest.put(C.ENDPOINTS.USER(id), getRequestValues(values));
    mutate();
    snackabr.show({ message: 'Saved successfully', severity: 'success' });
  };

  if (!user) return null;

  return (
    <div className="user-profile-container">
      <Form
        separatedLabels
        fields={fields}
        submitButtonId={'save_profile'}
        value={getValue(user)}
        onSubmit={handleSubmit}
        watch={['password']}
      />
    </div>
  );
};

export default General;
