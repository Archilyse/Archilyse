export default [
  { name: 'name', required: true, label: 'Competition name' },
  {
    name: 'red_flags_enabled',
    required: true,
    label: 'Red Flags enabled',
    type: 'dropdown',
    options: [
      { label: 'TRUE', value: 'true' },
      { label: 'FALSE', value: 'false' },
    ],
  },
  {
    name: 'currency',
    required: true,
    label: 'Currency',
    type: 'dropdown',
    options: [
      { label: 'EUR', value: 'EUR' },
      { label: 'CHF', value: 'CHF' },
    ],
  },
  {
    name: 'competitors',
    required: false,
    label: 'Competitors',
    type: 'dropdown',
    multiple: true,
    options: [],
  },
  {
    name: 'prices_are_rent',
    required: false,
    label: 'Prices from PH are rent or sale?',
    type: 'dropdown',
    options: [
      { label: 'RENT', value: 'true' },
      { label: 'SALE', value: 'false' },
    ],
  },
];
