import { MOCK_STATE } from '../tests/utils';
import { Prediction } from '../types';

export const SELECTED_LAYER_ID = 'layer-1';

export const MOCK_LINES = {
  '6217b7ff-6604-4bdc-bb85-da9257187cdd': {
    id: '6217b7ff-6604-4bdc-bb85-da9257187cdd',
    type: 'wall',
    prototype: 'lines',
    name: 'Wall',
    selected: false,
    properties: {
      referenceLine: 'OUTSIDE_FACE',
      height: { value: 300 },
      width: { value: 20 },
    },
    vertices: ['e9947e67-082f-48f3-8f8c-8bffd9a3e8b4', '2b5acfbe-e026-4317-b32d-57bc894be2be'],
    auxVertices: [],
    holes: [],
  },
  '822ed6d9-00d0-4381-9221-030acb62a740': {
    id: '822ed6d9-00d0-4381-9221-030acb62a740',
    type: 'wall',
    prototype: 'lines',
    name: 'Wall',
    selected: true,
    properties: {
      referenceLine: 'OUTSIDE_FACE',
      height: { value: 300 },
      width: { value: 20 },
    },
    vertices: ['2b5acfbe-e026-4317-b32d-57bc894be2be', 'f483af71-bd2b-4089-aa05-e9238d3942f1'],
    auxVertices: [],
    holes: [],
  },
};

export const MOCK_SNAP_ELEMENTS = [
  {
    type: 'point',
    x: 367,
    y: 1476,
    radius: 10,
    priority: 10,
    related: ['e9947e67-082f-48f3-8f8c-8bffd9a3e8b4'],
  },
  {
    type: 'line-segment',
    x1: 367,
    y1: 1476,
    x2: 908,
    y2: 1470,
    radius: 5,
    priority: 1,
    related: ['6217b7ff-6604-4bdc-bb85-da9257187cdd'],
  },
];

export const MOCK_EMPTY_SCENE = {
  ...MOCK_STATE.scene,
  layers: {
    [SELECTED_LAYER_ID]: {
      ...MOCK_STATE.scene.layers[SELECTED_LAYER_ID],
      vertices: {},
      lines: {},
      items: {},
    },
  },
  selectedLayer: SELECTED_LAYER_ID,
};

export const MOCK_DEMO_SCENE = {
  ...MOCK_EMPTY_SCENE,
  layers: {
    [SELECTED_LAYER_ID]: {
      ...MOCK_EMPTY_SCENE.layers[SELECTED_LAYER_ID],
      lines: MOCK_LINES,
    },
  },
};

export const MOCK_SCENE_HISTORY = {
  list: [MOCK_EMPTY_SCENE],
  first: MOCK_EMPTY_SCENE,
  last: MOCK_EMPTY_SCENE,
};

export const MOCK_SCALING_SCENE = {
  ...MOCK_EMPTY_SCENE,
  layers: {
    [SELECTED_LAYER_ID]: {
      ...MOCK_EMPTY_SCENE.layers[SELECTED_LAYER_ID],
      vertices: {
        '536fefb0-3c85-4c3e-96e8-ccde181968c1': {
          id: '536fefb0-3c85-4c3e-96e8-ccde181968c1',
          x: 1701.671126166495,
          y: 503.050505603978,
          lines: ['e769ae40-a321-476a-9d7b-2d3bacaa08c7'],
        },
        '7ad1f332-5920-4af5-8798-d09e666e7521': {
          id: '7ad1f332-5920-4af5-8798-d09e666e7521',
          x: 1498.238339685012,
          y: 674.523898716985,
          lines: ['dfab6dfe-7844-4594-ba27-dce2c2a7b2ce'],
        },
        'a7bb99cb-174d-4d0e-a29d-9b03fab4e98f': {
          id: 'a7bb99cb-174d-4d0e-a29d-9b03fab4e98f',
          x: 1300.884034739861,
          y: 516.842603418422,
          lines: ['e769ae40-a321-476a-9d7b-2d3bacaa08c7'],
        },
        'cf72aa91-deee-4388-b263-febec4217f84': {
          id: 'cf72aa91-deee-4388-b263-febec4217f84',
          x: 1484.446241873722,
          y: 530.307428823742,
          lines: ['dfab6dfe-7844-4594-ba27-dce2c2a7b2ce'],
        },
        '8ee1e1c0-d0d3-46f7-bba8-20004e6ef0c1': {
          id: '8ee1e1c0-d0d3-46f7-bba8-20004e6ef0c1',
          x: 1314.676132554305,
          y: 674.523898716985,
          lines: ['e6908a30-f9f0-48d4-88fb-b9cb1086e2e6'],
        },
        '74c02e24-c089-4a09-858b-7772330e0d18': {
          id: '74c02e24-c089-4a09-858b-7772330e0d18',
          x: 1470.654144059278,
          y: 530.307428823441,
          lines: ['dfab6dfe-7844-4594-ba27-dce2c2a7b2ce'],
        },
        '5042d80b-c0d7-42f4-a3fd-a594d0a9bbfd': {
          id: '5042d80b-c0d7-42f4-a3fd-a594d0a9bbfd',
          x: 1700.335169195073,
          y: 688.315996531429,
          lines: ['a9f41e6a-7281-456d-8c3a-a8bf8725f79e'],
        },
        'f9d6afeb-5c71-4ca9-b78c-a8c272d8e7cd': {
          id: 'f9d6afeb-5c71-4ca9-b78c-a8c272d8e7cd',
          x: 1300.884034739861,
          y: 503.050505603978,
          lines: ['e769ae40-a321-476a-9d7b-2d3bacaa08c7'],
        },
        'bcc73817-7c08-4057-96a8-0973a32ef5bb': {
          id: 'bcc73817-7c08-4057-96a8-0973a32ef5bb',
          x: 1687.879622782183,
          y: 530.506652321517,
          lines: ['721c9103-72b1-41f8-8b65-94d611529c4c'],
        },
        '57ca6bbe-ab73-49db-88a9-dd099e12df53': {
          id: '57ca6bbe-ab73-49db-88a9-dd099e12df53',
          x: 1674.088119397871,
          y: 530.378603410169,
          lines: ['721c9103-72b1-41f8-8b65-94d611529c4c'],
        },
        '39890e8b-e68a-41f1-bb66-0161304705ed': {
          id: '39890e8b-e68a-41f1-bb66-0161304705ed',
          x: 1470.654144056124,
          y: 674.523898716382,
          lines: ['dfab6dfe-7844-4594-ba27-dce2c2a7b2ce'],
        },
        '4c146252-77d0-4664-8510-4d91818f0fe1': {
          id: '4c146252-77d0-4664-8510-4d91818f0fe1',
          x: 1484.446241870568,
          y: 674.523898716683,
          lines: ['dfab6dfe-7844-4594-ba27-dce2c2a7b2ce'],
        },
        '92f2ff44-0d8e-49dc-83a6-3359d0b0bc31': {
          id: '92f2ff44-0d8e-49dc-83a6-3359d0b0bc31',
          x: 1498.238339688166,
          y: 530.307428824044,
          lines: ['dfab6dfe-7844-4594-ba27-dce2c2a7b2ce'],
        },
        '9a50ced1-de55-4a97-8ee1-1d1681d9744c': {
          id: '9a50ced1-de55-4a97-8ee1-1d1681d9744c',
          x: 1700.335169195073,
          y: 674.523898716985,
          lines: ['a9f41e6a-7281-456d-8c3a-a8bf8725f79e', '721c9103-72b1-41f8-8b65-94d611529c4c'],
        },
        '0b64205f-9272-4384-893d-f4d6d014a1ce': {
          id: '0b64205f-9272-4384-893d-f4d6d014a1ce',
          x: 1300.884034739861,
          y: 530.634701232866,
          lines: ['e769ae40-a321-476a-9d7b-2d3bacaa08c7', 'e6908a30-f9f0-48d4-88fb-b9cb1086e2e6'],
        },
        '5ff8e111-d91b-463d-a5a4-cd799ea3a89b': {
          id: '5ff8e111-d91b-463d-a5a4-cd799ea3a89b',
          x: 1700.335169195073,
          y: 702.108094345873,
          lines: ['a9f41e6a-7281-456d-8c3a-a8bf8725f79e'],
        },
        '7574f79a-915b-4517-ba7f-a1a7e80a4877': {
          id: '7574f79a-915b-4517-ba7f-a1a7e80a4877',
          x: 1701.671126166495,
          y: 516.842603418422,
          lines: ['e769ae40-a321-476a-9d7b-2d3bacaa08c7'],
        },
        '237cfc74-b238-4889-b6a1-ce50d1fab17f': {
          id: '237cfc74-b238-4889-b6a1-ce50d1fab17f',
          x: 1672.752162426449,
          y: 674.267800894288,
          lines: ['721c9103-72b1-41f8-8b65-94d611529c4c'],
        },
        '06b612dd-6835-4b5d-ad18-01e584b18392': {
          id: '06b612dd-6835-4b5d-ad18-01e584b18392',
          x: 1300.884034739861,
          y: 688.315996531429,
          lines: ['a9f41e6a-7281-456d-8c3a-a8bf8725f79e'],
        },
        'df0c2164-b04d-4f59-b200-f781014cb7f7': {
          id: 'df0c2164-b04d-4f59-b200-f781014cb7f7',
          x: 1328.468230368749,
          y: 530.634701232866,
          lines: ['e6908a30-f9f0-48d4-88fb-b9cb1086e2e6'],
        },
        '1bbea49c-1b7c-444a-9c56-495783de1bf6': {
          id: '1bbea49c-1b7c-444a-9c56-495783de1bf6',
          x: 1686.543665810761,
          y: 674.395849805636,
          lines: ['721c9103-72b1-41f8-8b65-94d611529c4c'],
        },
        'dbde9a56-c68f-42d2-99df-9177f4a42b78': {
          id: 'dbde9a56-c68f-42d2-99df-9177f4a42b78',
          x: 1300.884034739861,
          y: 674.523898716985,
          lines: ['a9f41e6a-7281-456d-8c3a-a8bf8725f79e', 'e6908a30-f9f0-48d4-88fb-b9cb1086e2e6'],
        },
        'bc1488af-7d5c-43c2-a319-dc32a62cc7df': {
          id: 'bc1488af-7d5c-43c2-a319-dc32a62cc7df',
          x: 1300.884034739861,
          y: 702.108094345873,
          lines: ['a9f41e6a-7281-456d-8c3a-a8bf8725f79e'],
        },
        'bda871a4-c7f5-4d42-9f52-9c4fa9177b6f': {
          id: 'bda871a4-c7f5-4d42-9f52-9c4fa9177b6f',
          x: 1701.671126166495,
          y: 530.634701232866,
          lines: ['e769ae40-a321-476a-9d7b-2d3bacaa08c7', '721c9103-72b1-41f8-8b65-94d611529c4c'],
        },
        'f3b82890-e4ec-49d0-9c32-745e834eeae1': {
          id: 'f3b82890-e4ec-49d0-9c32-745e834eeae1',
          x: 1328.468230368749,
          y: 674.523898716985,
          lines: ['e6908a30-f9f0-48d4-88fb-b9cb1086e2e6'],
        },
        '9efc4bec-8e2c-4090-8179-e9af915a10e9': {
          id: '9efc4bec-8e2c-4090-8179-e9af915a10e9',
          x: 1314.676132554305,
          y: 530.634701232866,
          lines: ['e6908a30-f9f0-48d4-88fb-b9cb1086e2e6'],
        },
      },
      lines: {
        'a9f41e6a-7281-456d-8c3a-a8bf8725f79e': {
          id: 'a9f41e6a-7281-456d-8c3a-a8bf8725f79e',
          prototype: 'lines',
          type: 'wall',
          properties: {
            referenceLine: 'OUTSIDE_FACE',
            height: {
              value: 300,
            },
            width: {
              value: 20,
            },
          },
          vertices: ['bc1488af-7d5c-43c2-a319-dc32a62cc7df', '5ff8e111-d91b-463d-a5a4-cd799ea3a89b'],
          auxVertices: [
            '06b612dd-6835-4b5d-ad18-01e584b18392',
            '5042d80b-c0d7-42f4-a3fd-a594d0a9bbfd',
            'dbde9a56-c68f-42d2-99df-9177f4a42b78',
            '9a50ced1-de55-4a97-8ee1-1d1681d9744c',
          ],
        },
        'e769ae40-a321-476a-9d7b-2d3bacaa08c7': {
          id: 'e769ae40-a321-476a-9d7b-2d3bacaa08c7',
          prototype: 'lines',
          type: 'wall',
          properties: {
            referenceLine: 'INSIDE_FACE',
            height: {
              value: 300,
            },
            width: {
              value: 20,
            },
          },
          vertices: ['f9d6afeb-5c71-4ca9-b78c-a8c272d8e7cd', '536fefb0-3c85-4c3e-96e8-ccde181968c1'],
          auxVertices: [
            'a7bb99cb-174d-4d0e-a29d-9b03fab4e98f',
            '7574f79a-915b-4517-ba7f-a1a7e80a4877',
            '0b64205f-9272-4384-893d-f4d6d014a1ce',
            'bda871a4-c7f5-4d42-9f52-9c4fa9177b6f',
          ],
        },
        'e6908a30-f9f0-48d4-88fb-b9cb1086e2e6': {
          id: 'e6908a30-f9f0-48d4-88fb-b9cb1086e2e6',
          prototype: 'lines',
          type: 'wall',
          properties: {
            referenceLine: 'OUTSIDE_FACE',
            height: {
              value: 300,
            },
            width: {
              value: 20,
            },
          },
          vertices: ['0b64205f-9272-4384-893d-f4d6d014a1ce', 'dbde9a56-c68f-42d2-99df-9177f4a42b78'],
          auxVertices: [
            '9efc4bec-8e2c-4090-8179-e9af915a10e9',
            '8ee1e1c0-d0d3-46f7-bba8-20004e6ef0c1',
            'df0c2164-b04d-4f59-b200-f781014cb7f7',
            'f3b82890-e4ec-49d0-9c32-745e834eeae1',
          ],
        },
        '721c9103-72b1-41f8-8b65-94d611529c4c': {
          id: '721c9103-72b1-41f8-8b65-94d611529c4c',
          prototype: 'lines',
          type: 'wall',
          properties: {
            referenceLine: 'OUTSIDE_FACE',
            height: {
              value: 300,
            },
            width: {
              value: 20,
            },
          },
          vertices: ['9a50ced1-de55-4a97-8ee1-1d1681d9744c', 'bda871a4-c7f5-4d42-9f52-9c4fa9177b6f'],
          auxVertices: [
            '1bbea49c-1b7c-444a-9c56-495783de1bf6',
            'bcc73817-7c08-4057-96a8-0973a32ef5bb',
            '237cfc74-b238-4889-b6a1-ce50d1fab17f',
            '57ca6bbe-ab73-49db-88a9-dd099e12df53',
          ],
        },
        'dfab6dfe-7844-4594-ba27-dce2c2a7b2ce': {
          id: 'dfab6dfe-7844-4594-ba27-dce2c2a7b2ce',
          prototype: 'lines',
          type: 'wall',
          properties: {
            referenceLine: 'OUTSIDE_FACE',
            height: {
              value: 300,
            },
            width: {
              value: 20,
            },
          },
          vertices: ['7ad1f332-5920-4af5-8798-d09e666e7521', '92f2ff44-0d8e-49dc-83a6-3359d0b0bc31'],
          auxVertices: [
            '4c146252-77d0-4664-8510-4d91818f0fe1',
            'cf72aa91-deee-4388-b263-febec4217f84',
            '39890e8b-e68a-41f1-bb66-0161304705ed',
            '74c02e24-c089-4a09-858b-7772330e0d18',
          ],
        },
      },
    },
  },
};

export const MOCK_PREDICTION: Prediction = {
  lines: [],
  holes: [
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [395, 3797],
            [483, 7669],
            [458, 7670],
            [270, 3799],
            [395, 3797],
          ],
        ],
      },
      properties: {
        label: 'DOOR',
      },
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [306, 6115],
            [315, 6205],
            [340, 6202],
            [331, 6113],
            [306, 6115],
          ],
        ],
      },
      properties: {
        label: 'WINDOW',
      },
    },
  ],
  items: [
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [732, 2845],
            [785, 2845],
            [785, 2710],
            [732, 2710],
            [732, 2845],
          ],
        ],
      },
      properties: {
        label: 'BATHTUB',
      },
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [724, 2695],
            [960, 2695],
            [960, 2640],
            [724, 2640],
            [724, 2695],
          ],
        ],
      },
      properties: {
        label: 'KITCHEN',
      },
    },
  ],
};
