import { render, screen } from '@testing-library/react';
import { GoToPipelineRenderer } from '../components';
import { C } from '../common';

let props;

const renderComponent = (changedProps = {}) => {
  props = { data: { id: 1 }, enforceMasterPlan: false, thereIsAMasterPlan: false, ...changedProps };
  return render(GoToPipelineRenderer(props));
};

it('Renders a link pointing always to the editor address', () => {
  renderComponent(props);
  expect(screen.getByText('Go to pipeline')).toBeInTheDocument();
  expect(screen.getByRole('link')).toHaveAttribute('href', C.URLS.EDITOR(1));
});

describe('With master plan workflow enforced', () => {
  it('Renders a text ("disabled link") if there is not a master plan', () => {
    renderComponent({ enforceMasterPlan: true, thereIsAMasterPlan: false });
    expect(screen.getByText('Go to pipeline')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('Renders a link if there is a master plann ', () => {
    renderComponent({ enforceMasterPlan: true, thereIsAMasterPlan: true });
    expect(screen.getByText('Go to pipeline')).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', C.URLS.EDITOR(1));
  });
});
