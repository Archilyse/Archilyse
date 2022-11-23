import React from 'react';
import { render, screen } from '@testing-library/react';
import { MOCK_SCENE } from '../../tests/utils';
import { COLORS, ITEM_STROKE_WIDTH } from '../../constants';
import { Item } from '../../class/export';
import ItemFactory from './item-factory';

const MOCK_ELEMENT = {
  prototype: 'items',
  name: 'playstation',
  type: 'playstation',
  selected: true,
  properties: {
    width: { value: 50, unit: 'cm' },
    length: { value: 60, unit: 'cm' },
  },
  x: 1013,
  y: 1758,
  rotation: 0,
};

const MOCK_INFO = {
  name: 'playstation',
  title: 'Playstation',
  description: 'La maquinita',
  image: '',
};

const setupElement = options => {
  const properties = {
    length: options.defaultLength ? { value: options.defaultLength, unit: 'cm' } : MOCK_ELEMENT.properties.length,
    width: options.defaultWidth ? { value: options.defaultWidth, unit: 'cm' } : MOCK_ELEMENT.properties.width,
  };

  const element = { ...MOCK_ELEMENT, selected: options.selected, properties: properties };
  return element;
};

const MockItemPositionValid = isValid => {
  jest.spyOn(Item, 'isSelectedItemInValidPosition');
  Item.isSelectedItemInValidPosition.mockImplementation(() => {
    return isValid;
  });
};

describe('ItemFactory', () => {
  const renderComponent = options => {
    const element = setupElement(options);
    const layer = {};
    const scene = MOCK_SCENE;
    const Item = props => ItemFactory('toilet', MOCK_INFO, options).render2D(element, layer, scene);
    return render(<Item />);
  };

  it('Can be used to create elements', async () => {
    renderComponent({});
    expect(screen.getByText(MOCK_INFO.name)).toBeInTheDocument();
  });

  it('Can be used to create elements with custom look & feel', async () => {
    const RECT_STYLE = { fill: 'grey' };
    const customLength = 100;
    const defaultWidth = MOCK_ELEMENT.properties.width.value;

    renderComponent({ defaultLength: customLength, rectStyle: RECT_STYLE });
    expect(screen.getByText(MOCK_INFO.name)).toBeInTheDocument();
    expect(screen.getByRole('presentation')).toHaveStyle(RECT_STYLE);
    // In svg rendered item we have width & height
    expect(screen.getByRole('presentation')).toHaveAttribute('height', String(customLength - ITEM_STROKE_WIDTH));
    expect(screen.getByRole('presentation')).toHaveAttribute('width', String(defaultWidth - ITEM_STROKE_WIDTH));
  });

  it.each([
    [true, true, ITEM_STROKE_WIDTH, COLORS.CATALOG.DEFAULT],
    [false, true, ITEM_STROKE_WIDTH, COLORS.CATALOG.DEFAULT],
    [true, false, ITEM_STROKE_WIDTH, COLORS.INVALID],
    [false, false, ITEM_STROKE_WIDTH, COLORS.CATALOG.DEFAULT],
  ])('Applies different style if item is selected or not', (isSelected, isValid, strokeWidth, color) => {
    MockItemPositionValid(isValid);
    renderComponent({ selected: isSelected });
    expect(screen.getByRole('presentation')).toHaveStyle({ 'stroke-width': strokeWidth, fill: color });
  });
});
