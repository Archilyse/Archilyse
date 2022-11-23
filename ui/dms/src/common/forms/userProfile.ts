/*eslint no-useless-escape: warn */

const validateRepeatedPassword = ({ password, repeated_password }) => {
  if (repeated_password !== password) {
    return "Password doesn't match";
  }
};

const validateEmail = ({ email }) => {
  const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  const valid = re.test(String(email).toLowerCase());
  if (!valid) {
    return 'Email is not valid';
  }
};

export default [
  { name: 'name', id: 'edit_profile_name', label: 'Full name', disabled: true },
  { name: 'roles', id: 'edit_profile_role', label: 'Role', disabled: true },
  { name: 'email', id: 'edit_profile_email', label: 'Email address', required: true, validate: validateEmail },
  {
    name: 'password',
    id: 'edit_profile_password',
    label: 'Password',
    type: 'password',
    passwordValidation: true,
    InputProps: { inputProps: { autoComplete: 'new-password' } },
  },
  {
    name: 'repeated_password',
    id: 'edit_profile_repeated_password',
    label: 'Repeat password',
    type: 'password',
    InputProps: { inputProps: { autoComplete: 'new-password' } },
    validate: validateRepeatedPassword,
    visible: values => Boolean(values.password),
  },
];
