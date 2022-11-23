import { MOCK_STATE } from '../tests/utils';
import { cloneDeep } from '../utils/export';

const MOCK_LINES = {
  '7e1c5af9-39a0-4204-80b0-add94bbbdf21': {
    id: '7e1c5af9-39a0-4204-80b0-add94bbbdf21',
    type: 'wall',
    prototype: 'lines',
    name: 'Wall',
    selected: false,
    properties: {
      height: {
        unit: 'cm',
        value: 300,
      },
      referenceLine: 'OUTSIDE_FACE',
      width: {
        unit: 'cm',
        value: 20,
      },
    },
    vertices: ['aa2fa193-ab56-4761-b634-388b85ae54ff', '45785c98-7455-419b-be8b-372b8155ae58'],
    auxVertices: [
      '1a875d10-f1c8-4851-be93-0806ba962c26',
      '938fca39-5a4d-41b9-bf1c-00fea4666842',
      '392932cb-53d3-4ff6-b5bf-966b240155dc',
      '9db41fda-7edc-4f83-a7f8-349f52177ab8',
    ],
    holes: ['cd9114ce-7fca-4523-a72e-8e3f1c074ea5'],
    coordinates: [
      [
        [360.307693970492, 1039.07911863776],
        [546.180752250087, 1039.07911863776],
        [546.180752250087, 1059.07911863776],
        [360.307693970492, 1059.07911863776],
        [360.307693970492, 1039.07911863776],
      ],
    ],
  },
  'c5f07d45-a5c5-4d3e-8efe-9563f61d3d86': {
    id: 'c5f07d45-a5c5-4d3e-8efe-9563f61d3d86',
    type: 'wall',
    prototype: 'lines',
    name: 'Wall',
    selected: false,
    properties: {
      height: {
        unit: 'cm',
        value: 300,
      },
      referenceLine: 'OUTSIDE_FACE',
      width: {
        unit: 'cm',
        value: 20,
      },
    },
    vertices: ['4a0ade18-0cc5-46e7-b585-882a70d38a7b', 'bffda6da-ae32-435d-96c8-c99db43f0413'],
    auxVertices: [
      '9a2b166e-5e18-425b-b7b1-d990d9bc184f',
      'fc51f2db-7e3b-4684-8795-6413c52ba8ad',
      'b532b4f5-d060-453b-9b75-656dabf83ea7',
      '4c4b1400-08d8-4123-94fb-550695d45264',
    ],
    holes: [],
    coordinates: [
      [
        [364.279340514928, 1108.185768510943],
        [546.180752250087, 1108.185768510943],
        [546.180752250087, 1128.185768510943],
        [364.279340514928, 1128.185768510943],
        [364.279340514928, 1108.185768510943],
      ],
    ],
  },
};

const MOCK_VERTICES = {
  '938fca39-5a4d-41b9-bf1c-00fea4666842': {
    id: '938fca39-5a4d-41b9-bf1c-00fea4666842',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 546.180752250087,
    y: 1050.173612117535,
    lines: ['7e1c5af9-39a0-4204-80b0-add94bbbdf21'],
  },
  'fc51f2db-7e3b-4684-8795-6413c52ba8ad': {
    id: 'fc51f2db-7e3b-4684-8795-6413c52ba8ad',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 546.180752250087,
    y: 1119.280261990718,
    lines: ['c5f07d45-a5c5-4d3e-8efe-9563f61d3d86'],
  },
  '4a0ade18-0cc5-46e7-b585-882a70d38a7b': {
    id: '4a0ade18-0cc5-46e7-b585-882a70d38a7b',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 364.279340514928,
    y: 1128.185768510943,
    lines: ['c5f07d45-a5c5-4d3e-8efe-9563f61d3d86'],
  },
  'aa2fa193-ab56-4761-b634-388b85ae54ff': {
    id: 'aa2fa193-ab56-4761-b634-388b85ae54ff',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 546.180752250087,
    y: 1059.07911863776,
    lines: ['7e1c5af9-39a0-4204-80b0-add94bbbdf21'],
  },
  '392932cb-53d3-4ff6-b5bf-966b240155dc': {
    id: '392932cb-53d3-4ff6-b5bf-966b240155dc',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 360.307693970492,
    y: 1041.268105597311,
    lines: ['7e1c5af9-39a0-4204-80b0-add94bbbdf21'],
  },
  '9a2b166e-5e18-425b-b7b1-d990d9bc184f': {
    id: '9a2b166e-5e18-425b-b7b1-d990d9bc184f',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 364.279340514928,
    y: 1119.280261990718,
    lines: ['c5f07d45-a5c5-4d3e-8efe-9563f61d3d86'],
  },
  '4c4b1400-08d8-4123-94fb-550695d45264': {
    id: '4c4b1400-08d8-4123-94fb-550695d45264',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 546.180752250087,
    y: 1110.374755470493,
    lines: ['c5f07d45-a5c5-4d3e-8efe-9563f61d3d86'],
  },
  '9db41fda-7edc-4f83-a7f8-349f52177ab8': {
    id: '9db41fda-7edc-4f83-a7f8-349f52177ab8',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 546.180752250087,
    y: 1041.268105597311,
    lines: ['7e1c5af9-39a0-4204-80b0-add94bbbdf21'],
  },
  'bffda6da-ae32-435d-96c8-c99db43f0413': {
    id: 'bffda6da-ae32-435d-96c8-c99db43f0413',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 546.180752250087,
    y: 1128.185768510943,
    lines: ['c5f07d45-a5c5-4d3e-8efe-9563f61d3d86'],
  },
  'b532b4f5-d060-453b-9b75-656dabf83ea7': {
    id: 'b532b4f5-d060-453b-9b75-656dabf83ea7',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 364.279340514928,
    y: 1110.374755470493,
    lines: ['c5f07d45-a5c5-4d3e-8efe-9563f61d3d86'],
  },
  '1a875d10-f1c8-4851-be93-0806ba962c26': {
    id: '1a875d10-f1c8-4851-be93-0806ba962c26',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 360.307693970492,
    y: 1050.173612117535,
    lines: ['7e1c5af9-39a0-4204-80b0-add94bbbdf21'],
  },
  '45785c98-7455-419b-be8b-372b8155ae58': {
    id: '45785c98-7455-419b-be8b-372b8155ae58',
    type: '',
    prototype: 'vertices',
    name: 'Vertex',
    selected: false,
    properties: {},
    x: 360.307693970492,
    y: 1059.07911863776,
    lines: ['7e1c5af9-39a0-4204-80b0-add94bbbdf21'],
  },
};

const MOCK_ITEMS = {
  '68f8dd38-3449-43a6-8299-07eedf38c5da': {
    id: '68f8dd38-3449-43a6-8299-07eedf38c5da',
    type: 'seat',
    prototype: 'items',
    name: 'Seat',
    selected: false,
    properties: {
      altitude: {
        unit: 'cm',
        value: 0,
      },
      length: {
        unit: 'cm',
        value: 62,
      },
      width: {
        unit: 'cm',
        value: 51,
      },
    },
    x: 350,
    y: 1000,
    rotation: 0,
  },
  'd2ae555c-a6f7-40d4-b75f-53fcc9d1c2cd': {
    id: 'd2ae555c-a6f7-40d4-b75f-53fcc9d1c2cd',
    type: 'kitchen',
    prototype: 'items',
    name: 'Kitchen',
    selected: false,
    properties: {
      altitude: {
        unit: 'cm',
        value: 0,
      },
      length: {
        unit: 'cm',
        value: 82,
      },
      width: {
        unit: 'cm',
        value: 58,
      },
    },
    x: 390,
    y: 950,
    rotation: 0,
  },
};

export const MOCK_HOLES = {
  'cd9114ce-7fca-4523-a72e-8e3f1c074ea5': {
    id: 'cd9114ce-7fca-4523-a72e-8e3f1c074ea5',
    type: 'door',
    prototype: 'holes',
    name: 'Door',
    selected: false,
    properties: {
      altitude: {
        unit: 'cm',
        value: 0,
      },
      flip_horizontal: false,
      flip_vertical: true,
      heights: {
        lower_edge: null,
        upper_edge: null,
      },
      length: {
        unit: 'cm',
        value: 80,
      },
      width: {
        unit: 'cm',
        value: 30,
      },
    },
    offset: 0.34195431116007763,
    line: '7e1c5af9-39a0-4204-80b0-add94bbbdf21',
    coordinates: [
      [
        [360.51494277881403, 1023.2912736246634],
        [360.51494277881403, 1041.188560375337],
        [360.51494277881403, 1041.188560375337],
        [432.104089781508, 1023.2912736246634],
        [432.104089781508, 1041.188560375337],
      ],
    ],
    door_sweeping_points: {
      angle_point: [432.104089781508, 1032.239917],
      closed_point: [360.51494277881403, 1032.239917],
      opened_point: [432.104089781508, 1103.829064002694],
    },
  },
};

const MOCK_STATE_WITH_TWO_LINES = cloneDeep(MOCK_STATE);
const SELECTED_LAYER_ID = MOCK_STATE_WITH_TWO_LINES.scene.selectedLayer;

MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines = MOCK_LINES;
MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].vertices = MOCK_VERTICES;
MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items = MOCK_ITEMS;
MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].holes = MOCK_HOLES;

export { MOCK_STATE_WITH_TWO_LINES, SELECTED_LAYER_ID };
