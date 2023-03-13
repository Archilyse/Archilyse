export default [
  { name: 'name', label: 'Site Name', disabled: true },
  { name: 'client_site_id', label: 'Client Site Id', disabled: true, required: true },
  { name: 'client_id', label: 'Client Id', disabled: true },
  {
    name: 'client_target_id',
    required: true,
    label: 'Select Target Client',
    type: 'dropdown',
    options: [],
  },
];
