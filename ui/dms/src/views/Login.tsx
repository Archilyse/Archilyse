import React from 'react';
import { Form, PublicFormsContainer, useLogin } from 'archilyse-ui-components';
import { Link } from 'react-router-dom';
import { C } from '../common';

import { getInitialPageUrlByRole } from '../common/modules';
import { ActionsType, checkAccess } from '../common/roles';
import fields from '../common/forms/login';
import './login.scss';

const Login = () => {
  const { handleSubmit } = useLogin({
    getInitialPageUrl: getInitialPageUrlByRole,
    checkAccess: intent => checkAccess(intent as ActionsType),
  });

  return (
    <PublicFormsContainer>
      <h2 className="public-forms-title">Sign in</h2>
      <p>If you have an account with us, please sign in</p>
      <Form
        id={'login-user-form'}
        fields={fields}
        onSubmit={handleSubmit}
        SubmitButton={() => (
          <button id="login-dms-user" className="secondary-button large" type="submit">
            Sign in
          </button>
        )}
        separatedLabels
      />
      <Link to={C.URLS.FORGOT_PASSWORD()} className="forgot-password-link">
        Forgot password?
      </Link>
    </PublicFormsContainer>
  );
};

export default Login;
