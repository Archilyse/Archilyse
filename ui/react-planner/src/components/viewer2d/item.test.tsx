import { Scene } from '../../models';
import { MOCK_SCENE } from '../../tests/utils';
import MyCatalog from '../../catalog-elements/mycatalog';
import { areEqual } from './item';

const LAYER_ID = 'layer-1';

describe('Item component', () => {
  let props;
  beforeEach(() => {
    const mockScene = new Scene(MOCK_SCENE);
    const layer = mockScene.layers[LAYER_ID];
    const item = Object.values(layer.items)[0];

    props = {
      item,
      layer,
      scene: mockScene,
      catalog: MyCatalog,
    };
  });

  it('Should not render if properties are not changed', () => {
    expect(areEqual(props, props)).toEqual(true);
  });

  it('Should render if properties are changed', () => {
    const updatedProps = {
      ...props,
    };

    updatedProps.item = {
      ...updatedProps.item,
      x: 300,
    };
    expect(areEqual(props, updatedProps)).toEqual(false);
  });
});
