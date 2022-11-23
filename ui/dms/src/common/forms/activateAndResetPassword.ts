const validateRepeatedPassword = ({ password, repeated_password }) => {
  if (repeated_password !== password) {
    return "Password doesn't match";
  }
};

export default [
  {
    name: 'password',
    label: 'New password',
    placeholder: 'Enter new password',
    type: 'password',
    required: true,
    passwordValidation: true,
    InputProps: { inputProps: { autoComplete: 'new-password' } },
  },
  {
    name: 'repeated_password',
    label: 'Repeat new password',
    placeholder: 'Repeat new password',
    type: 'password',
    required: true,
    InputProps: { inputProps: { autoComplete: 'new-password' } },
    validate: validateRepeatedPassword,
  },
];
