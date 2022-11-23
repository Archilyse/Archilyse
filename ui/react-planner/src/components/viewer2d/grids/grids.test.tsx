import { Scene } from '../../../models';
import { MOCK_SCENE } from '../../../tests/utils';
import { areEqual } from './grids';

describe('Grids component', () => {
  let props;
  beforeEach(() => {
    MOCK_SCENE.grids = {
      h1: {
        id: 'h1',
        type: 'horizontal-streak',
        properties: {
          step: 20,
          colors: ['#808080', '#ddd', '#ddd', '#ddd', '#ddd'],
        },
      },
      v1: {
        id: 'v1',
        type: 'vertical-streak',
        properties: {
          step: 20,
          colors: ['#808080', '#ddd', '#ddd', '#ddd', '#ddd'],
        },
      },
    };
    const mockScene = new Scene(MOCK_SCENE);
    props = {
      scene: mockScene,
    };
  });

  it('Should not render if props are not changed', () => {
    expect(areEqual(props, props)).toEqual(true);
  });

  it.each([
    ['width', 3500, null],
    ['height', 2500, null],
    // ['grids', 25, 'grids/h1/properties/step'],
  ])('Should render if %s prop is changed', (key, value, path) => {
    const updatedProps = {
      ...props,
    };

    const newScene = {
      false: {
        ...updatedProps.scene,
        [key]: value,
      },
      true: {
        ...updatedProps.scene,
        grids: {
          ...updatedProps.scene.grids,
          h1: {
            ...updatedProps.scene.grids.h1,
            properties: {
              ...updatedProps.scene.grids.h1.properties,
              step: value,
            },
          },
        },
      },
    };
    const hasPath = String(!!path);
    updatedProps.scene = newScene[hasPath];

    expect(areEqual(props, updatedProps)).toEqual(false);
  });
});
