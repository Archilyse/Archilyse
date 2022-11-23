import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import RenameDialog from './RenameDialog';

describe('RenameDialog', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<RenameDialog {...props} />);
  };
  beforeEach(() => {
    props = {
      open: true,
      onClose: jest.fn(),
      onRename: jest.fn(),
      label: 'File name',
      name: 'image.png',
    };
  });
  it('shows dialog if open is true', async () => {
    const { queryByTestId } = renderComponent();
    expect(queryByTestId('rename-dialog')).toBeInTheDocument();
  });
  it('does not show dialog if open is false', () => {
    const { queryByTestId } = renderComponent({ open: false });
    expect(queryByTestId('formrename-dialog')).not.toBeInTheDocument();
  });
  it('sets the name as default text in the input', () => {
    const { queryByLabelText } = renderComponent();
    // @ts-ignore @TODO: replace with something that works
    expect(queryByLabelText('File name').value).toEqual('image.png');
  });
  it('calls onRename when accept is clicked', () => {
    const { queryByText } = renderComponent();
    fireEvent.click(queryByText('Accept'));
    expect(props.onRename).toHaveBeenCalledWith('image.png');
  });
  it('calls onRename when "enter" is pressed', () => {
    const { queryByLabelText } = renderComponent();
    fireEvent.keyPress(queryByLabelText('File name'), {
      keyCode: 13,
    });
    expect(props.onRename).toHaveBeenCalledWith('image.png');
  });
  it('runs onClose when cancel is clicked', () => {
    const { queryByText } = renderComponent();
    fireEvent.click(queryByText('Cancel'));
    expect(props.onClose).toHaveBeenCalled();
  });
});
