import { waitFor, screen } from '@testing-library/react';

const TABLE_TEST_ID = 'ag-grid-table';
const WAIT_FOR_TABLE_MS = 10000;

const isTableLoaded = async () => screen.queryByTestId(TABLE_TEST_ID);

const visibleCustomRenderers = (container, minCustomRenders) => {
  const customRenders = container.querySelectorAll('.ag-react-container');
  const renders = Array.prototype.slice.call(customRenders);
  expect(renders.length >= minCustomRenders).toBeTruthy();
};

// We have to specify the nr of custom cell renderers in the given table to wait for them.
export default async (container, minCustomRenders) => {
  await waitFor(() => isTableLoaded, { timeout: WAIT_FOR_TABLE_MS });
  await waitFor(() => visibleCustomRenderers(container, minCustomRenders), { timeout: WAIT_FOR_TABLE_MS });
};
