import React, { useEffect } from 'react';
import { auth, Form, PublicFormsContainer, useLogin } from 'archilyse-ui-components';
import { URLS } from '../../constants';
import C from '../../../../common/src/constants';
import 'archilyse-ui-components/dist/styles.css';
import './login.scss';
import { ProviderMetrics } from '../../providers';

const EDITOR_BACKGROUND_COLOR = '#445f86';
const ALLOWED_ROLES = [C.ROLES.ADMIN, C.ROLES.TEAMMEMBER, C.ROLES.TEAMLEADER];

const fields = [
  { name: 'user', label: 'User', required: true },
  { name: 'password', label: 'Password', type: 'password', required: true },
];

const Login = () => {
  const { handleSubmit } = useLogin({
    getInitialPageUrl: URLS.HOME,
    checkAccess: _ => auth.hasValidRole(ALLOWED_ROLES),
  });

  useEffect(() => {
    ProviderMetrics.trackPageView();
  }, []);

  return (
    <PublicFormsContainer appTitle={'Editor v2'} backgroundColor={EDITOR_BACKGROUND_COLOR}>
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
