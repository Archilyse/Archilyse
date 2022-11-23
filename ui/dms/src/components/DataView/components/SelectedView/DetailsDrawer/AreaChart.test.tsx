import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { C } from '../../../../../common';
import AreaChart from './AreaChart';

const MOCK_AREA_DATA = {
  floors: [
    { id: '12522', netArea: 390.84278479898046, name: 'Floor 0' },
    { id: '12523', netArea: 601.1704691159182, name: 'Floor 1' },
    { id: '12524', netArea: 604.9551220302199, name: 'Floor 2' },
    { id: '12525', netArea: 608.2619054347667, name: 'Floor 3' },
    { id: '12526', netArea: 605.6258426751153, name: 'Floor 4' },
  ],
};

const MOCK_VISIBLE_ITEMS = [
  { id: '12522', type: 'folder-floors', name: 'Floor 0' },
  { id: '12523', type: 'folder-floors', name: 'Floor 1' },
  { id: '12524', type: 'folder-floors', name: 'Floor 2' },
  { id: '12525', type: 'folder-floors', name: 'Floor 3' },
  { id: '12526', type: 'folder-floors', name: 'Floor 4' },
];

describe('Analysis Chart component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<AreaChart {...props} />);
  };
  beforeEach(() => {
    props = {
      areaData: MOCK_AREA_DATA,
      visibleItems: MOCK_VISIBLE_ITEMS,
    };
  });

  const totalSurface = MOCK_AREA_DATA.floors.reduce((accum, f) => accum + f.netArea, 0);
  const getExpectedSurface = surface => `${surface.toFixed(1)}m2`;
  const HOVERED_FILE = { id: '123', name: 'fake-file', type: C.MIME_TYPES.PDF };
  const [firstFloor] = MOCK_AREA_DATA.floors;
  const HOVERED_FLOOR = { id: firstFloor.id, name: firstFloor.name, type: 'folder-floors' };

  it.each([
    [null, getExpectedSurface(totalSurface)],
    [HOVERED_FLOOR, getExpectedSurface(MOCK_AREA_DATA.floors[0].netArea)],
    [HOVERED_FILE, getExpectedSurface(totalSurface)],
  ])('Displays the expected surface for: %o', async (hoveredItem, expectedSurface) => {
    renderComponent({ hoveredItem });
    expect(screen.getByText(expectedSurface)).toBeInTheDocument();
  });

  it('Can hover over a chart item', async () => {
    const onHoverPieChartItem = jest.fn();
    const PIE_CHART_HTML_ELEMENT = 'path';

    const { container } = renderComponent({ onHoverPieChartItem });
    fireEvent.mouseEnter(container.querySelector(PIE_CHART_HTML_ELEMENT)); // Nasty
    expect(onHoverPieChartItem).toHaveBeenCalled();
  });
});
