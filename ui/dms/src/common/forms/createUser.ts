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
  { name: 'name', id: 'create_user_name', label: 'Full name', placeholder: 'Enter full name' },
  { name: 'login', id: 'create_user_login', required: true, label: 'Login', placeholder: 'Enter login name' },
  {
    name: 'email',
    id: 'create_user_email',
    required: true,
    label: 'Email address',
    placeholder: 'Enter email address',
    validate: validateEmail,
  },
  {
    name: 'roles',
    id: 'create_user_roles',
    required: true,
    label: 'Roles',
    type: 'dropdown',
    options: [],
    multiple: false,
    placeholder: 'Select role',
  },
  {
    name: 'password',
    id: 'create_user_password',
    required: true,
    label: 'Password',
    type: 'password',
    placeholder: 'Enter password',
    passwordValidation: true,
    InputProps: { inputProps: { autoComplete: 'new-password' } },
  },
  {
    name: 'repeated_password',
    id: 'create_user_repeated_password',
    label: 'Repeat password',
    type: 'password',
    placeholder: 'Repeat password',
    InputProps: { inputProps: { autoComplete: 'new-password' } },
    validate: validateRepeatedPassword,
    visible: values => Boolean(values.password),
  },
];
