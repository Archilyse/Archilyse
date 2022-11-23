import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { MOCK_CONTEXT, MOCK_STATE } from '../../tests/utils';
import { getMockState } from '../../tests/utils/tests-utils';
import { PanelImportAnnotations } from './panel-import-annotations';
import * as f from './panel-import-annotations-helper';

jest.mock('react-router-dom', () => ({
  // @ts-ignore
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn().mockReturnValue({ id: '2' }),
}));

describe('Import Annotations tests', () => {
  const mockedState = {
    ...MOCK_STATE,
    siteStructure: {
      floors: [
        { building_id: 1, floor_number: -1, plan_id: 2, plan_ready: true },
        { building_id: 1, floor_number: 0, plan_id: 3, plan_ready: true },
        { building_id: 1, floor_number: 1, plan_id: MOCK_CONTEXT.planId, plan_ready: false }, //current plan
        { building_id: 1, floor_number: 2, plan_id: 4, plan_ready: false },
        { building_id: 1, floor_number: 3, plan_id: 4, plan_ready: false },
        { building_id: 2, floor_number: 0, plan_id: 5, plan_ready: true },
      ],
    },
  };

  let store;
  const mockStore = configureStore();
  const renderComponent = () => {
    return render(
      <Provider store={store}>
        {/* @ts-ignore */}
        <PanelImportAnnotations />
      </Provider>
    );
  };

  beforeEach(() => {
    const state = { 'react-planner': getMockState(mockedState) };
    store = mockStore(state);
  });

  afterEach(() => {
    store.clearActions();
  });

  it('Trying to import an annotation which is not ready', () => {
    const loadProjectSpy = jest.spyOn(f, 'reloadProject');
    renderComponent();

    const importButtonName = 'Import Annotation';

    const select = screen.getByDisplayValue('');
    userEvent.selectOptions(select, '2');

    const importButton = screen.getByText(importButtonName);
    userEvent.click(importButton);
    expect(loadProjectSpy).not.toBeCalled();
  });

  it('Importing an annotation', () => {
    const loadProjectSpy = jest.spyOn(f, 'reloadProject');
    renderComponent();

    const importButtonName = 'Import Annotation';

    const select = screen.getByDisplayValue('');
    userEvent.selectOptions(select, '0');

    const importButton = screen.getByText(importButtonName);
    userEvent.click(importButton);
    expect(loadProjectSpy).toBeCalled();
  });
});
