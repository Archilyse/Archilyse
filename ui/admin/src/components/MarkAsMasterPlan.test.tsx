import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderRequest } from 'Providers';
import { MarkAsMasterPlanRenderer } from './MarkAsMasterPlan';

let props;

afterEach(() => {
  jest.clearAllMocks();
});

const renderComponent = (changedProps = {}) => {
  props = { data: { id: 1 }, site: { enforce_masterplan: true }, reloadPipelines: () => {}, ...changedProps };
  return render(MarkAsMasterPlanRenderer(props));
};

it('Renders a checkbox that can be clicked', () => {
  renderComponent(props);

  const checkbox = screen.getByRole('checkbox');

  expect(checkbox).toBeInTheDocument();
  expect(checkbox).not.toBeDisabled();
});

it('Renders a disabled checkbox if masterplan workflow is not enforced', () => {
  renderComponent({ site: { enforce_masterplan: false } });

  const checkbox = screen.getByRole('checkbox');

  expect(checkbox).toBeInTheDocument();
  expect(checkbox).toBeDisabled();
});

describe('Masterplan size check', () => {
  const SELECTED_PLAN = { id: 1, image_height: 1000, image_width: 2000 };
  const BIGGER_PLAN = { id: 2, image_height: 3000, image_width: 2000 };
  const SMALLER_PLAN = { id: 3, image_height: 500, image_width: 500 };

  let MOCK_SNACKBAR;
  beforeEach(() => {
    jest.spyOn(ProviderRequest, 'put').mockImplementation(async url => ({}));
    MOCK_SNACKBAR = { show: jest.fn() };
  });

  it('Shows a warning when selecting a masterplan smaller than other plan', async () => {
    const MOCK_PLANS = [SELECTED_PLAN, BIGGER_PLAN];
    jest.spyOn(Promise, 'all').mockImplementation(async url => MOCK_PLANS);

    renderComponent({
      data: { id: SELECTED_PLAN.id },
      pipelines: [{ id: SELECTED_PLAN.id }, { id: BIGGER_PLAN.id }],
      snackbar: MOCK_SNACKBAR,
    });

    const checkbox = screen.getByRole('checkbox');
    userEvent.click(checkbox);

    const EXPECTED_SNACKBAR = {
      message: `The selected master plan is smaller than the plans: {${BIGGER_PLAN.id}}, this may affect the labelling`,
      severity: 'warning',
    };
    await waitFor(() => expect(MOCK_SNACKBAR.show).toHaveBeenCalledWith(EXPECTED_SNACKBAR));
  });

  it('Does not show a warning when selecting a masterplan bigger than every other plan', async () => {
    const MOCK_PLANS = [SELECTED_PLAN, SMALLER_PLAN];
    jest.spyOn(Promise, 'all').mockImplementation(async url => MOCK_PLANS);

    renderComponent({
      data: { id: SELECTED_PLAN.id },
      pipelines: [{ id: SELECTED_PLAN.id }, { id: SMALLER_PLAN.id }],
      snackbar: MOCK_SNACKBAR,
    });

    const checkbox = screen.getByRole('checkbox');
    userEvent.click(checkbox);

    await waitFor(() => expect(MOCK_SNACKBAR.show).not.toHaveBeenCalled());
  });
});
