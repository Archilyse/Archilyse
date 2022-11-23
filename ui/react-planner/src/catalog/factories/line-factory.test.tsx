import React from 'react';
import { render, screen } from '@testing-library/react';
import { MOCK_SCENE } from '../../tests/utils';
import { REFERENCE_LINE_POSITION } from '../../constants';
import { Layer, Line } from '../../models';
import { GeometryUtils, PolygonUtils } from '../../utils/export';
import LineFactory from './line-factory';

const MOCK_ELEMENT = {
  prototype: 'lines',
  holes: [],
  selected: false,
  properties: {
    width: { value: 1 },
    height: { value: 1 },
    referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
  },
  coordinates: [
    [
      [0, 0],
      [5, 0],
      [5, 3],
      [0, 3],
      [0, 0],
    ],
  ],
  name: 'a nice wall',
  type: 'wall',
  id: 'line',
  vertices: ['one', 'two'],
  auxVertices: ['three', 'four', 'five', 'six'],
};

const MOCK_INFO = {
  name: 'some nice wall',
  title: 'awol',
  description: 'test',
  image: '',
};

const setupElement = (options: any = {}) => {
  const newProperties = {
    ...MOCK_ELEMENT.properties,
    ...options.properties,
  };

  return new Line({
    ...MOCK_ELEMENT,
    ...options,
    properties: newProperties,
    vertices: MOCK_ELEMENT.vertices,
    coordinates: MOCK_ELEMENT.coordinates,
  }) as any;
};

const renderComponent = (options: any = {}) => {
  let element = setupElement(options);
  let widthCM = 1;
  let [v0, v1] = [
    { id: 'one', x: 0, y: 0 },
    { id: 'two', x: 1, y: 1 },
  ];

  if (options.vertices) {
    [v0, v1] = options.vertices;
  }

  if (options.properties?.width?.value) {
    widthCM = options.properties.width.value;
  }

  const points = { x1: v0.x, x2: v1.x, y1: v0.y, y2: v1.y };
  const pointToVertex = ([x, y]) => ({ x, y });
  const widthPX = GeometryUtils.convertCMToPixels(1, widthCM);

  const [av1, av2] = GeometryUtils.getParallelLinePointsFromOffset(points, widthPX / 2).map(pointToVertex);
  const [av3, av4] = GeometryUtils.getParallelLinePointsFromOffset(points, widthPX).map(pointToVertex);

  const vertices = {
    one: v0,
    two: v1,
    three: av1,
    four: av2,
    five: av3,
    six: av4,
  };
  const line = { id: 'line', vertices: ['one', 'two'], auxVertices: ['three', 'four', 'five', 'six'] };

  element = {
    ...element,
    vertices: line.vertices,
    auxVertices: line.auxVertices,
  };

  const layer = new Layer({
    vertices,
    lines: { line: line },
  });
  const scene = MOCK_SCENE;
  const shouldRenderRulerAndAngle = true;
  const Line = props =>
    LineFactory('column', MOCK_INFO, options).render2D(element, layer, scene, shouldRenderRulerAndAngle);
  return render(<Line />);
};

describe('LineFactory', () => {
  it('Can be used to adjusted look & feel of line elements', async () => {
    const RECT_STYLE = { fill: 'red' };
    renderComponent({ styleRect: RECT_STYLE });

    expect(screen.getByRole('presentation')).toHaveStyle(RECT_STYLE);
  });

  it('Line is properly rendered with the given coordinates', () => {
    const coordinates = [
      [
        [0, 0],
        [5, 0],
        [5, 3],
        [0, 3],
        [0, 0],
      ],
    ];
    renderComponent();
    const polygon = screen.getByRole('presentation');
    expect(polygon).toHaveAttribute('points', PolygonUtils.coordsToSVGPoints(coordinates));
  });

  // @TODO: Add non-rectangle polygon test
});

describe('getAngle', () => {
  it.each([
    [
      [
        { id: 'one', x: 0, y: 0 },
        { id: 'two', x: 0, y: 1 },
      ],
      '90.00°',
    ],
    [
      [
        { id: 'one', x: 0, y: 0 },
        { id: 'two', x: 0, y: -1 },
      ],
      '90.00°',
    ],
    [
      [
        { id: 'one', x: 0, y: 0 },
        { id: 'two', x: 1, y: 0 },
      ],
      '0.00°',
    ],
    [
      [
        { id: 'one', x: 0, y: 0 },
        { id: 'two', x: -1, y: 0 },
      ],
      '0.00°',
    ],
    [
      [
        { id: 'one', x: 0, y: 0 },
        { id: 'two', x: 1, y: 1 },
      ],
      '45.00°',
    ],
    [
      [
        { id: 'one', x: 0, y: 0 },
        { id: 'two', x: -1, y: -1 },
      ],
      '45.00°',
    ],
  ])('Displays always the rotation (0, 90) when the element is selected', (vertices, expectedAngle) => {
    renderComponent({ vertices, selected: true });
    const line = screen.getByTestId(`viewer-line-${MOCK_ELEMENT.id}-angle`);
    expect(line).toHaveTextContent(expectedAngle);
  });

  it('Does not display the rotation angle when the element is not selected', () => {
    const vertices = [
      { id: 'one', x: 0, y: 0 },
      { id: 'two', x: 0, y: 1 },
    ];
    renderComponent({ vertices, selected: false });
    expect(screen.queryByTestId(`viewer-line-${MOCK_ELEMENT.id}-angle`)).not.toBeInTheDocument();
  });
});
