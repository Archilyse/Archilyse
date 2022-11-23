import * as React from 'react';
import { cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import Widget from './index';

afterEach(cleanup);

const MOCK_CONTENT_1 = 'Wonderful tab content 1';
const MOCK_CONTENT_2 = 'Wonderful tab content 2';

it('renders correctly with two tabs', () => {
  const { container } = render(
    <Widget className={'view-drawer'} tabHeaders={['Tab 1', 'Tab 2']}>
      <p>{MOCK_CONTENT_1}</p>
      <p>{MOCK_CONTENT_2}</p>
    </Widget>
  );
  expect(container).toMatchSnapshot();
});

it('change tabs successfully', async () => {
  const { getByText } = render(
    <Widget className={'view-drawer'} tabHeaders={['Tab 1', 'Tab 2']}>
      <p>{MOCK_CONTENT_1}</p>
      <p>{MOCK_CONTENT_2}</p>
    </Widget>
  );
  const isTabVisible = tabContent => getByText(tabContent);

  expect(isTabVisible(MOCK_CONTENT_1)).toBeTruthy();

  // Switch tab and ensure the content has changed
  fireEvent.click(getByText('Tab 2'));

  await waitFor(() => expect(isTabVisible(MOCK_CONTENT_2)).toBeTruthy());
  expect(isTabVisible(MOCK_CONTENT_2)).toBeTruthy();
});
