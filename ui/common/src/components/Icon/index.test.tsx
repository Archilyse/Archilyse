import React from 'react';
import { render } from '@testing-library/react';
import Icon from '.';

describe('Icon Component', () => {
  let props: any = {};

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<Icon {...props} />);
  };

  beforeEach(() => {
    props.children = '';
  });

  it('renders a custom icon when the children is in the list of custom icons', () => {
    props.children = 'logo';
    const { queryByText } = renderComponent();
    expect(queryByText('logo')).not.toBeInTheDocument();
  });
  it('renders a font icon when the children is not in the list of custom icons', () => {
    props.children = 'image';
    const { queryByText } = renderComponent();
    expect(queryByText('image')).toBeInTheDocument();
  });
});
