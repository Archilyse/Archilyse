import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { SNAP_MASK } from '../../utils/snap';
import { getMockState } from '../../tests/utils/tests-utils';
import { Models as PlannerModels } from '../../export'; //react-planner
import FooterBar from './footerbar';

const AppState = {
  'react-planner': new PlannerModels.State(),
};

jest.mock('react-router-dom', () => ({
  useParams() {
    return jest.fn();
  },
}));

jest.mock('../../hooks/useSvgPlanTransforms.ts', () => {
  return {
    __esModule: true,
    useSvgPlanTransforms: jest.fn().mockReturnValue({ zoom: 1, transformX: 0, transformY: 0 }),
  };
});

const INITIAL_MASK = SNAP_MASK;

describe('Footerbar component', () => {
  let props;
  let store;
  const mockStore = configureStore();
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    store = mockStore(AppState);
    return render(
      <Provider store={store}>
        <FooterBar {...props} />
      </Provider>
    );
  };

  beforeEach(() => {
    const newState = { 'react-planner': getMockState({ snapMask: SNAP_MASK }) };
    store = mockStore(newState);
    props = {
      width: 120,
      height: 30,
    };
  });

  afterEach(() => {
    store.clearActions();
  });

  it.each([
    ['Snap PT', { SNAP_POINT: !INITIAL_MASK.SNAP_POINT }],
    ['Snap SEG', { SNAP_SEGMENT: !INITIAL_MASK.SNAP_SEGMENT }],
  ])('Clicking on the button %s toggles the snap', async (text, snapToToggle) => {
    renderComponent();
    const footerBarButton = screen.getByText(new RegExp(text));
    expect(footerBarButton).toBeInTheDocument();
    userEvent.click(footerBarButton);

    const expectedNewSnapMask = { ...INITIAL_MASK, ...snapToToggle };
    const [dispatchedAction] = store.getActions();
    expect(dispatchedAction.mask.SNAP_POINT).toBe(expectedNewSnapMask.SNAP_POINT);
    expect(dispatchedAction.mask.SNAP_SEGMENT).toBe(expectedNewSnapMask.SNAP_SEGMENT);
  });
});
