const validateRepeatedPassword = ({ password, repeated_password }) => {
  if (repeated_password !== password) {
    return "Password doesn't match";
  }
};

export default [
  {
    name: 'password',
    label: 'New password',
    type: 'password',
    required: true,
    InputProps: { inputProps: { autoComplete: 'new-password' } },
  },
  {
    name: 'repeated_password',
    label: 'Repeat new password',
    type: 'password',
    required: true,
    InputProps: { inputProps: { autoComplete: 'new-password' } },
    validate: validateRepeatedPassword,
  },
];
