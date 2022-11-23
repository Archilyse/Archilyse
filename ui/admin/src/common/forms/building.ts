export default [
  { name: 'housenumber', required: true, label: 'House Number' },
  {
    name: 'client_building_id',
    required: false,
    label: 'Client Building ID',
  },
  { name: 'city', required: true, label: 'City' },
  { name: 'zipcode', required: true, label: 'Zipcode' },
  { name: 'street', required: true, label: 'Street' },
  { name: 'elevation', label: 'Elevation', disabled: true },
];
