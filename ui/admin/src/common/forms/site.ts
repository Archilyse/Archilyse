export default [
  { name: 'name', required: true, label: 'Site name' },
  { name: 'client_site_id', label: 'Client Site Id' },
  { name: 'region', required: true, label: 'Region' }, // This could be a dropdown in the future
  {
    name: 'lon',
    label: 'Longitude',
    validate: formValues => validateCoord('lon', formValues),
    InputProps: { min: -180, max: 180 },
    placeholder: 'From -180 to 180',
  },
  {
    name: 'lat',
    label: 'Latitude',
    validate: formValues => validateCoord('lat', formValues),
    InputProps: { min: -90, max: 90 },
    placeholder: 'From -90 to 90',
  },
  {
    name: 'priority',
    type: 'number',
    label: 'Priority (1=lowest, 10=highest)',
    required: true,
    InputProps: { min: 1, max: 10 },
    placeholder: 'From 1 to 10',
  },
  {
    name: 'simulation_version',
    type: 'dropdown',
    options: [
      { label: 'Yes', value: 'PH_01_2021' },
      { label: 'No', value: 'PH_2022_H1' },
    ],
    required: true,
    label: 'CustomValuator pricing required?',
  },
  { name: 'raw_dir', label: 'Raw Dir' },
  { name: 'ifc', label: 'IFC (optional)', type: 'file', multiple: true, accept: '.ifc' },
  { name: 'qa_id', type: 'hidden' },
];

const validateCoord = (coord, formValues) => {
  const hasData = formValues[coord];
  const hasIfcFile = formValues.ifc && formValues.ifc.length > 0;
  return Boolean(hasData || hasIfcFile);
};
