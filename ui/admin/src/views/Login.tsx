import React from 'react';
import { Form, PublicFormsContainer, useLogin } from 'archilyse-ui-components';
import { getInitialPageUrlByRole } from '../common/modules';
import { ActionsType, checkAccess } from '../common/roles';
import fields from '../common/forms/login';
import './login.scss';

const ADMIN_BACKGROUND_COLOR = '#445f86';

const Login = () => {
  const { handleSubmit } = useLogin({
    getInitialPageUrl: getInitialPageUrlByRole,
    checkAccess: intent => checkAccess(intent as ActionsType),
  });

  return (
    <PublicFormsContainer appTitle="Admin" backgroundColor={ADMIN_BACKGROUND_COLOR}>
      <h2 className="public-forms-title">Sign in</h2>
      <Form
        fields={fields}
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
