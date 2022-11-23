import React from 'react';
import { Form, PublicFormsContainer, useLogin } from 'archilyse-ui-components';
import { C } from 'Common';
import { ActionsType, checkAccess } from '../common/roles';

const FIELDS = [
  { name: 'user', label: 'User', required: true },
  { name: 'password', label: 'Password', type: 'password', required: true },
];

const Login = () => {
  const { handleSubmit } = useLogin({
    getInitialPageUrl: C.URLS.HOME,
    checkAccess: intent => checkAccess(intent as ActionsType),
  });

  return (
    <PublicFormsContainer appTitle="Potential Simulations">
      <h2 className="public-forms-title">Sign in</h2>
      <Form
        fields={FIELDS}
        onSubmit={handleSubmit}
        SubmitButton={() => (
          <button className="secondary-button large" type="submit">
            Sign in
          </button>
        )}
      />
    </PublicFormsContainer>
  );
};

export default Login;
