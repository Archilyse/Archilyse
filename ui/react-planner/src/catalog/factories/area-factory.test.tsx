import React from 'react';
import { render, screen } from '@testing-library/react';
import { MOCK_AREA, MOCK_SCENE } from '../../tests/utils';
import * as SharedStyle from '../../shared-style';
import AreaFactory from './area-factory';

const MOCK_INFO = {
  title: 'area',
  description: 'Generic Room',
  image: '',
};

describe('AreaFactory', () => {
  const renderComponent = options => {
    const element = { ...MOCK_AREA, ...options };
    const layer = { vertices: MOCK_SCENE.layers['layer-1'].vertices };
    const scene = {};
    const Area = props => AreaFactory('area', MOCK_INFO, options.areaType).render2D(element, layer, scene);
    return render(<Area />);
  };

  it('Creates area elements with default fill and opacity', () => {
    renderComponent({});
    const areaElement = screen.getByRole('presentation');
    expect(areaElement).toHaveAttribute('fill-opacity', SharedStyle.AREA_MESH_OPACITY.unselected.toFixed(1));
    expect(areaElement).toHaveAttribute('fill', SharedStyle.AREA_MESH_COLOR.unselected);
  });

  it('Creates area elements that has specific fill and opacity upon selection', () => {
    renderComponent({ selected: true });
    const areaElement = screen.getByRole('presentation');
    expect(areaElement).toHaveAttribute('fill-opacity', SharedStyle.AREA_MESH_OPACITY.selected.toFixed(1));
    expect(areaElement).toHaveAttribute('fill', SharedStyle.AREA_MESH_COLOR.selected);
  });
});
