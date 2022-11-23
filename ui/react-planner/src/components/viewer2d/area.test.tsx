import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MOCK_AREA, MOCK_SCENE } from '../../tests/utils';
import AreaFactory from '../../catalog/factories/area-factory';
import Area from './area';

const MOCK_INFO = {
  title: 'area',
  description: 'Generic Room',
  image: '',
};

const MOCK_SCALE = 2;

jest.mock('../../hooks/useSvgPlanTransforms.ts', () => {
  return {
    getCurrentZoomLvl: () => 0.23456,
  };
});

describe('Area component', () => {
  let catalog;
  let props;
  const mode = 'not scaling';
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };

    return render(<Area {...props} />);
  };

  const setupArea = (properties: any = undefined, coords: Array<any> = undefined, isScaleArea: any = false) => {
    let newArea = MOCK_AREA as any;
    const areaProperties = properties || MOCK_AREA.properties;
    const areaCoords = coords || MOCK_AREA.coords;

    newArea = {
      ...newArea,
      properties: {
        ...newArea.properties,
        ...areaProperties,
      },
      coords: areaCoords,
      ['isScaleArea']: isScaleArea,
    };
    return newArea;
  };

  const setupLayer = (lines = undefined) => {
    return {
      vertices: MOCK_SCENE.layers['layer-1'].vertices,
      lines: lines || MOCK_SCENE.layers['layer-1'].lines,
    };
  };

  beforeEach(() => {
    props = {
      scale: MOCK_SCALE,
    };
    catalog = { getElement: jest.fn(() => AreaFactory('area', MOCK_INFO, 'bathroom')) };
  });

  it('Should display area size in sq.m.', () => {
    const layer = setupLayer();
    const area = setupArea();

    renderComponent({ layer: layer, area: area, catalog: catalog, mode: mode, scaleTool: {} });
    const renderedArea = screen.getByTestId(`viewer-area-${area.id}`);
    expect(renderedArea).toBeInTheDocument();
    expect(renderedArea).toHaveTextContent('12.26 m²');
  });

  it('Should display area size of the scale tool if the area has been created in scaling', () => {
    const MOCK_SCALE_TOOL = { areaSize: 4.21 };
    const isScaleArea = true;
    const layer = setupLayer();
    const area = setupArea(null, null, isScaleArea);

    renderComponent({ layer: layer, area: area, catalog: catalog, mode: mode, scaleTool: MOCK_SCALE_TOOL });
    const renderedArea = screen.getByTestId(`viewer-area-${area.id}`);
    expect(renderedArea).toBeInTheDocument();
    expect(renderedArea).toHaveTextContent(`${MOCK_SCALE_TOOL.areaSize} m²`);
  });

  it('Should display room stamp', () => {
    const areaType = 'MANCAVE';
    const layer = setupLayer();
    const area = setupArea({ areaType: areaType });

    renderComponent({ layer: layer, area: area, catalog: catalog, mode: mode, scaleTool: {} });
    const renderedArea = screen.getByTestId(`viewer-area-${MOCK_AREA.id}`);
    expect(renderedArea).toBeInTheDocument();
    expect(renderedArea).toHaveTextContent(areaType);
  });
});
