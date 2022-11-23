import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import NewFolderDialog from './NewFolderDialog';

describe('NewFolderDialog', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<NewFolderDialog {...props} />);
  };
  beforeEach(() => {
    props = {
      open: true,
      onClose: jest.fn(),
      onAccept: jest.fn(),
    };
  });
  it('shows dialog if open is true', async () => {
    const { queryByTestId } = renderComponent();
    expect(queryByTestId('new-folder-dialog')).toBeInTheDocument();
  });
  it('does not show dialog if open is false', () => {
    const { queryByTestId } = renderComponent({ open: false });
    expect(queryByTestId('new-folder-dialog')).not.toBeInTheDocument();
  });
  it('calls onAccept when accept is clicked', () => {
    const { queryByText, queryByLabelText } = renderComponent();
    // @ts-ignore @TODO: replace with something that works
    queryByLabelText('Folder name').value = 'my folder';
    fireEvent.click(queryByText('Accept'));
    expect(props.onAccept).toHaveBeenCalledWith('my folder');
  });
  it('calls onAccept when "enter" is pressed', () => {
    const { queryByLabelText } = renderComponent();
    // @ts-ignore @TODO: replace with something that works
    queryByLabelText('Folder name').value = 'my folder';
    fireEvent.keyPress(queryByLabelText('Folder name'), {
      keyCode: 13,
    });
    expect(props.onAccept).toHaveBeenCalledWith('my folder');
  });
  it('runs onClose when cancel is clicked', () => {
    const { queryByText } = renderComponent();
    fireEvent.click(queryByText('Cancel'));
    expect(props.onClose).toHaveBeenCalled();
  });
});
