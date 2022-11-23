export default {
  NEW: [
    {
      name: 'floorplan',
      required: true,
      label: 'Floor plan',
      type: 'file',
      accept: 'image/png, image/jpeg, application/pdf',
    },
    {
      name: 'floor_lower_range',
      required: true,
      type: 'number',
      label: 'Lower value of the range',
      placeholder: '1 if there is only one floor',
    },
    {
      name: 'floor_upper_range',
      required: true,
      type: 'number',
      label: 'Upper value of the range',
      placeholder: 'Same as lower range if there is only one',
    },
  ],

  EDIT: [
    {
      name: 'floor_number',
      required: true,
      type: 'number',
      label: 'Floor Number',
    },
  ],
};
