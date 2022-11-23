import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Dropdown from '.';

const MOCK_OPTIONS = [
  {
    value: '',
    label: 'All floors',
  },
  {
    value: 1,
    label: 'Floor 1',
  },
  {
    value: 2,
    label: 'Floor 2',
  },
  {
    value: 3,
    label: 'Floor 3',
  },
];

const DropdownWrapper = () => {
  const [value, setValue] = React.useState('');

  return <Dropdown options={MOCK_OPTIONS} onChange={e => setValue(e.target.value)} value={value} />;
};

it('selects options as expected', async () => {
  render(<DropdownWrapper />);

  userEvent.click(screen.getByRole('button', { name: /all floors/i }));

  MOCK_OPTIONS.slice(1).forEach(option => {
    expect(screen.getByRole('option', { name: option.label })).toBeInTheDocument();
  });

  userEvent.click(screen.getByRole('option', { name: /floor 1/i }));
  expect(screen.getByRole('button', { name: /floor 1/i })).toBeInTheDocument();

  userEvent.click(screen.getByRole('button', { name: /floor 1/i }));
  userEvent.click(screen.getByRole('option', { name: /floor 3/i }));
  expect(screen.getByRole('button', { name: /floor 3/i })).toBeInTheDocument();
});
