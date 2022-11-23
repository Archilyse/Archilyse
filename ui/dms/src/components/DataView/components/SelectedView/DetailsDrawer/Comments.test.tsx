import React from 'react';
import { render, screen } from '@testing-library/react';
import { C } from 'Common';
import userEvent from '@testing-library/user-event';
import Comments from './Comments';

window.HTMLElement.prototype.scrollIntoView = jest.fn();

const MOCK_COMMENTS = [
  {
    comment: 'Here we are on this bright day',
    created: '2021-03-22T10:59:47.299070',
    creator: {
      name: 'Payaso 1',
    },
    creator_id: 86,
    file_id: 50,
    id: 31,
    updated: null,
  },
  {
    comment: 'Such a wonderful file',
    created: '2021-03-22T10:59:48.384119',
    creator: {
      name: 'Payaso 2',
    },
    creator_id: 86,
    file_id: 50,
    id: 32,
    updated: null,
  },
  {
    comment: 'And mysterious also',
    created: '2021-03-22T10:59:49.349326',
    creator: {
      name: 'Payaso 3',
    },
    creator_id: 86,
    file_id: 50,
    id: 33,
    updated: null,
  },
];

const mockPathname = C.DMS_VIEWS.SITES;

jest.mock('../../../../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
  usePrevious: () => {},
}));

describe('Comments component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<Comments {...props} />);
  };

  beforeEach(() => {
    props = {
      comments: [],
      onAddComments: () => {},
    };
  });

  it('Renders comments displaying author and comment messages', () => {
    renderComponent({ comments: MOCK_COMMENTS });
    expect(screen.queryAllByTestId('comment').length).toEqual(MOCK_COMMENTS.length);
    for (const comment of MOCK_COMMENTS) {
      expect(screen.getByText(comment.creator.name)).toBeInTheDocument();
      expect(screen.getByText(comment.comment)).toBeInTheDocument();
    }
  });

  it('Can write new comments', () => {
    const MOCK_COMMENT_TEXT = 'this is the best comment ever';
    const onAddComment = jest.fn();
    renderComponent({ onAddComment });

    userEvent.type(screen.getByLabelText('Add a comment & press enter'), MOCK_COMMENT_TEXT);
    expect(screen.getByText(new RegExp(MOCK_COMMENT_TEXT))).toBeInTheDocument();

    userEvent.type(screen.getByLabelText('Add a comment & press enter'), '{enter}');
    expect(onAddComment).toHaveBeenCalled();
  });
});
