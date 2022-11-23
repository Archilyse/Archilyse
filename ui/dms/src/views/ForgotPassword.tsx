import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { Form, Icon, PublicFormsContainer, SnackbarContext } from 'archilyse-ui-components';
import fields from '../common/forms/forgotPassword';
import { ProviderRequest } from '../providers';
import { C } from '../common';
import './forgotPassword.scss';

const BACK_ICON_COLOR = '#434C50';

const getRequestValues = values => ({
  email: values.email,
});

const ForgotPassword = () => {
  const snackbar = useContext(SnackbarContext);

  const handleSubmit = async values => {
    const params = { ...getRequestValues(values) };
    await ProviderRequest.put(C.ENDPOINTS.USER_FORGOTTEN_PASSWORD(), params);

    snackbar.show({
      message: 'Password reset request sent. Please check your email.',
      severity: 'success',
    });
  };

  return (
    <PublicFormsContainer>
      <h2 className="public-forms-title">Reset password</h2>
      <p className="forgot-password-info">
        Enter your email address below, <br />
        we will send you instructions on how to reset your password
      </p>
      <Form
        id={'reset-password-form'}
        fields={fields}
        onSubmit={handleSubmit}
        SubmitButton={() => (
          <button id="reset-password-btn" className="secondary-button large" type="submit">
            Submit
          </button>
        )}
        separatedLabels
      />
      <Link to={C.URLS.LOGIN()} className="forgot-password-link">
        <Icon style={{ marginRight: '8px', marginLeft: '0px', fontSize: '20px', color: BACK_ICON_COLOR }}>
          keyboard_backspace
        </Icon>
        Back to login
      </Link>
    </PublicFormsContainer>
  );
};

export default ForgotPassword;
