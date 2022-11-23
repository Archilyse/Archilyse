import * as React from 'react';
import { render, screen } from '@testing-library/react';
import * as SharedStyle from '../../shared-style';
import {
  CIRCLE_RADIUS,
  CIRCLE_RADIUS_REFERENCE,
  COLORS,
  VERTEX_DEFAULT_OPACITY,
  VERTEX_SCALING_OPACITY,
} from '../../constants';
import Vertex from './vertex';

describe('Vertex component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };

    return render(<Vertex {...props} />);
  };

  it('Renders an auxillary vertex of a line with default style', () => {
    const vertex = { id: 'x', x: 1, y: 1, lines: ['1'] };
    const layer = { lines: { '1': { vertices: ['a', 'b'], auxVertices: ['x', 'y'] } } };

    const { container } = renderComponent({ vertex: vertex, layer: layer, isScaling: false });
    expect(screen.getByTestId('vertex-x')).toBeInTheDocument();
    expect(container.querySelector('circle')).toHaveStyle({
      fill: COLORS.SELECTED_ELEMENT,
      fillOpacity: VERTEX_DEFAULT_OPACITY,
      stroke: SharedStyle.COLORS.white,
    });
    expect(container.querySelector('circle')).toHaveAttribute('r', CIRCLE_RADIUS);
  });

  it('Renders an enlarged vertex when it is a part of a line reference', () => {
    const vertex = { id: 'a', x: 1, y: 1, lines: ['1'] };
    const layer = { lines: { '1': { vertices: ['a', 'b'], auxVertices: ['x', 'y'], selected: true } } };

    const { container } = renderComponent({ vertex: vertex, layer: layer, isScaling: false });
    expect(container.querySelector('circle')).toHaveStyle({
      fill: COLORS.SELECTED_ELEMENT,
      fillOpacity: VERTEX_DEFAULT_OPACITY,
      stroke: SharedStyle.COLORS.dark_blue,
    });
    expect(container.querySelector('circle')).toHaveAttribute('r', CIRCLE_RADIUS_REFERENCE);
  });

  it('Renders transparently when is scaling', () => {
    const vertex = { id: 'x', x: 1, y: 1, lines: ['1'] };
    const layer = { lines: { '1': { vertices: ['a', 'b'], auxVertices: ['x', 'y'], selected: true } } };

    const { container } = renderComponent({ vertex: vertex, layer: layer, isScaling: true });
    expect(container.querySelector('circle')).toHaveStyle({
      fill: COLORS.SELECTED_ELEMENT,
      fillOpacity: VERTEX_SCALING_OPACITY,
      stroke: SharedStyle.COLORS.white,
    });
  });
});
