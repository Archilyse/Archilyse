import React, { useContext } from 'react';
import { Redirect } from 'react-router-dom';
import { Form, PublicFormsContainer, SnackbarContext } from 'archilyse-ui-components';
import { useRouter } from '../common/hooks';
import { C } from '../common';
import fields from '../common/forms/activateAndResetPassword';
import { ProviderRequest } from '../providers';
import './activateAndResetPassword.scss';

const getFinalMessage = message => (
  <>
    {message}{' '}
    <a href={`/${C.SERVER_BASENAME}${C.URLS.LOGIN()}`} className="go-to-login-link">
      Go to login page
    </a>
  </>
);

const getRequestValues = values => ({
  password: values.password,
});

const ActivateAndResetPassword = () => {
  const { query } = useRouter();

  const snackbar = useContext(SnackbarContext);

  const handleSubmit = async values => {
    // @TODO: decide is it creating or resetting password and create proper message
    const params = { ...getRequestValues(values), token: query.token };
    await ProviderRequest.put(C.ENDPOINTS.USER_RESET_PASSWORD(), params);

    const message = getFinalMessage('New password created successfully');
    snackbar.show({ message, severity: 'success' });
  };

  if (!query.token) {
    return <Redirect to={C.URLS.LOGIN()} />;
  }

  return (
    <PublicFormsContainer>
      <h2 className="public-forms-title">Set password</h2>
      <Form
        id={'activate-password-form'}
        fields={fields}
        onSubmit={handleSubmit}
        SubmitButton={() => (
          <button id="activate-password-btn" className="secondary-button large" type="submit">
            Activate
          </button>
        )}
        separatedLabels
      />
    </PublicFormsContainer>
  );
};

export default ActivateAndResetPassword;
