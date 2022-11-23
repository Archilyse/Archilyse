import React, { useState } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RequestStatus } from 'archilyse-ui-components';
import RequestForm from '.';

const StatefulWrapper = ({ children }) => {
  const [fields, setFields] = useState({});

  return React.cloneElement(children, { fields, onChange: setFields });
};

const waitToBeValid = async input => {
  await waitFor(async () => {
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(input).toBeValid();
  });
};

const waitToBeInvalid = async input => {
  await waitFor(async () => {
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(input).toBeInvalid();
  });
};

it.each([
  [
    [47, 7],
    [true, true],
  ],
  [
    [150, -200],
    [false, false],
  ],
])('Validation on %s numbers works as expected', async ([lat, lon], [isLatValid, isLonValid]) => {
  render(
    <StatefulWrapper>
      {/* @ts-ignore */}
      <RequestForm onSubmit={jest.fn()} requestState={{ data: null, status: RequestStatus.IDLE, error: null }} />
    </StatefulWrapper>
  );

  if (lat !== undefined) {
    const input = screen.getByRole('spinbutton', { name: 'Latitude:' });

    userEvent.type(input, String(lon));

    if (isLatValid) {
      await waitToBeValid(input);
    } else {
      await waitToBeInvalid(input);
    }
  }

  if (lon !== undefined) {
    const input = screen.getByRole('spinbutton', { name: 'Longitude:' });

    userEvent.type(input, String(lon));

    if (isLonValid) {
      await waitToBeValid(input);
    } else {
      await waitToBeInvalid(input);
    }
  }
});
