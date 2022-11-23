import { Scene } from '../../models';
import { MOCK_SCENE } from '../../tests/utils';

import MyCatalog from '../../catalog-elements/mycatalog';
import { OPENING_TYPE, PrototypesEnum } from '../../constants';
import { areEqual } from './line';

const LAYER_ID = 'layer-1';
const HOLE_ID = '103a3581-24d4-47a8-99ab-10b3e3d02ace';
let LINE_ID = null;

describe('Line component', () => {
  let props;
  beforeEach(() => {
    const mockScene = new Scene(MOCK_SCENE);
    let layer = mockScene.layers[LAYER_ID];
    LINE_ID = Object.keys(layer.lines)[0];

    const MOCK_HOLES = {
      [HOLE_ID]: {
        type: OPENING_TYPE.WINDOW,
        prototype: PrototypesEnum.HOLES,
        name: 'Window',
        selected: false,
        offset: 0.5477718140218387,
        coordinates: [],
        id: HOLE_ID,
        properties: {},
        line: LINE_ID,
      },
    };

    layer = {
      ...layer,
      holes: MOCK_HOLES,
    };

    props = {
      line: layer.lines[LINE_ID],
      layer,
      scene: mockScene,
      catalog: MyCatalog,
    };
  });

  it('Should not render if properties are not changed', () => {
    expect(areEqual(props, props)).toEqual(true);
  });

  it.each([
    ['scale', 2.0],
    ['unit', 'm'],
  ])('Should render if scene %s is changed', (key, value) => {
    const updatedProps = {
      ...props,
    };
    updatedProps.scene = {
      ...updatedProps.scene,
      [key]: value,
    };

    expect(areEqual(props, updatedProps)).toEqual(false);
  });

  it('Should render if line props are changed', () => {
    const updatedProps = {
      ...props,
    };
    updatedProps.line = {
      ...updatedProps.line,
      properties: {
        ...updatedProps.line.properties,
        height: {
          ...updatedProps.line.properties.height,
          value: 300,
        },
      },
    };
    expect(areEqual(props, updatedProps)).toEqual(false);
  });

  it('Should render if hole on the same line is changed', () => {
    const updatedProps = {
      ...props,
    };

    updatedProps.line = {
      ...updatedProps.line,
      holes: [HOLE_ID],
    };
    updatedProps.layer = {
      ...updatedProps.layer,
      holes: {
        ...updatedProps.layer.holes,
        [HOLE_ID]: {
          ...updatedProps.layer.holes[HOLE_ID],
          selected: true,
        },
      },
      selected: {
        ...updatedProps.layer.selected,
        holes: [HOLE_ID],
      },
    };

    expect(areEqual(props, updatedProps)).toEqual(false);
  });
  it('Should render if the holes of the layer changes', () => {
    const updatedProps = {
      ...props,
    };

    updatedProps.line.holes = ['newHole'];
    updatedProps.layer = {
      ...updatedProps.layer,
      holes: { newHole: { id: 'newHole' } },
    };

    expect(areEqual(props, updatedProps)).toEqual(false);
  });
});
