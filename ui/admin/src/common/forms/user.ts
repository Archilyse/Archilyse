export default [
  { name: 'client_id', label: 'Associated client', type: 'dropdown', options: [] },
  { name: 'group_id', label: 'Group', type: 'dropdown', options: [] },
  { name: 'name', label: 'Name' },
  { name: 'login', required: true, label: 'Login' },
  { name: 'email', required: true, label: 'Email' },
  { name: 'roles', required: true, label: 'Roles', type: 'dropdown', options: [], multiple: true },
  { name: 'password', required: true, label: 'Password', type: 'password', passwordValidation: true },
];
