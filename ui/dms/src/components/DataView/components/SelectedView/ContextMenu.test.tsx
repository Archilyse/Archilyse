import React from 'react';
import { render, screen } from '@testing-library/react';
import { C } from 'Common';
import ContextMenu from './ContextMenu';

const MOCK_FILE = { name: 'plan1', type: C.MIME_TYPES.JPEG, id: 1 };
const MOCK_FOLDER = { name: 'tol-folder', type: 'custom-folder', id: 1 };

const mockPathname = '/clients';

type TestCase = [typeof MOCK_FILE, typeof MOCK_FOLDER, boolean, string, string[]];

describe('ContextMenu component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<ContextMenu {...props} />);
  };

  beforeEach(() => {
    props = {
      open: true,
      clickedItem: null,
      itemInClipboard: null,
      pasteAllowed: true,
      pathname: mockPathname,
      handlers: {},
      onClose: () => {},
      anchorPosition: { top: 12, left: 10 },
    };
  });

  const TEST_CASES: TestCase[] = [
    [null, null, false, mockPathname, ['No contextual actions']],
    [null, MOCK_FILE, false, mockPathname, ['No contextual actions']],
    [null, MOCK_FILE, true, mockPathname, [`Paste ${MOCK_FILE.name} here`]],
    [MOCK_FILE, null, true, mockPathname, ['Cut', 'Details', 'Download', 'Delete', 'Rename']],
    [MOCK_FOLDER, null, true, mockPathname, ['Cut', 'Delete', 'Rename']],
    [MOCK_FOLDER, null, true, C.DMS_VIEWS.TRASH, ['Restore', 'Delete permanently']],
  ];

  it.each(TEST_CASES)(
    'Expected actions for item: %o, itemInClipboard: %o, pasteAllowed: %s pathname: %s',
    async (clickedItem, itemInClipboard, pasteAllowed, pathname, expectedActions) => {
      renderComponent({ clickedItem, itemInClipboard, pasteAllowed, pathname });
      expectedActions.forEach(action => {
        expect(screen.getByText(new RegExp(action))).toBeInTheDocument();
      });
    }
  );
});
