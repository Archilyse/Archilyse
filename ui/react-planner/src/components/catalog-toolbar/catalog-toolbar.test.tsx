import { getMockState } from '../../tests/utils/tests-utils';
import { areEqual } from './catalog-toolbar';

describe('Catalog toolbar component', () => {
  let props;
  beforeEach(() => {
    const mockState = getMockState();
    props = {
      state: mockState,
    };
  });

  it('Should not render if redux state changes', () => {
    const updatedProps = {
      ...props,
    };
    updatedProps.state = {
      ...updatedProps.state,
      zoom: 2,
    };

    expect(areEqual(props, updatedProps)).toEqual(true);
  });

  it('Should render if an element is selected', () => {
    const updatedProps = {
      ...props,
    };

    updatedProps.state = {
      ...updatedProps.state,
      drawingSupport: { type: 'Seat' },
    };
    expect(areEqual(props, updatedProps)).toEqual(false);
  });
});
