import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import Tags from './Tags';

describe('Tags Component', () => {
  let props: any = {};

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<Tags {...props} />);
  };

  beforeEach(() => {
    props.defaultValue = [''];
    props.onChange = jest.fn();
    props.editable = false;
    props.suggestions = [];
  });

  it('renders an add icon when "editable" is true', () => {
    props.editable = true;
    const { queryByTestId } = renderComponent();
    expect(queryByTestId('tags-add-circle-icon')).toBeInTheDocument();
  });
  it('renders an add icon when "editable" is false', () => {
    props.editable = false;
    const { queryByTestId } = renderComponent();
    expect(queryByTestId('tags-add-circle-icon')).toBeInTheDocument();
  });
  it('renders an add icon when "editable" is true but the text field is focused', () => {
    props.editable = true;
    const { queryByTestId } = renderComponent();
    fireEvent.focus(queryByTestId('tags-text-field'));
    expect(queryByTestId('tags-add-circle-icon')).toBeInTheDocument();
  });
  it('renders an add icon when "editable" is true and the text field is not focused after having been focused', () => {
    props.editable = true;
    const { queryByTestId } = renderComponent();
    fireEvent.focus(queryByTestId('tags-text-field'));
    fireEvent.blur(queryByTestId('tags-text-field'));
    expect(queryByTestId('tags-add-circle-icon')).toBeInTheDocument();
  });
});
