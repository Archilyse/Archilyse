import React from 'react';
import {
  CATALOG_ELEMENT_OPACITY,
  CATALOG_ELEMENT_OPACITY_SELECTED,
  COLORS,
  ITEM_STROKE_WIDTH,
  MEASURE_STEP_ITEM,
} from '../../constants';
import * as GeometryUtils from '../../utils/geometry';
import { Item } from '../../class/export';

type Info = {
  title: string;
  description: string;
  image: unknown;
};

type Options = {
  rectStyle?: any;
  defaultLength?: number;
  defaultWidth?: number;
  additionalProperties: any;
};

const ItemFactory = (
  name: string,
  info: Info,
  { rectStyle = {}, defaultLength = 50, defaultWidth = 50, additionalProperties = {} } = {} as Options
) => {
  const STYLE_ITEM_RECT = {
    opacity: CATALOG_ELEMENT_OPACITY,
    strokeWidth: ITEM_STROKE_WIDTH,
    stroke: COLORS.STROKE_NON_SELECTED_ITEM,
    fill: COLORS.CATALOG.DEFAULT,
  };
  const STYLE_ITEM_RECT_SELECTED = {
    ...STYLE_ITEM_RECT,
    opacity: CATALOG_ELEMENT_OPACITY_SELECTED,
    stroke: COLORS.SELECTED_ELEMENT,
  };
  const STYLE_ITEM_RECT_SELECTED_INVALID = {
    ...STYLE_ITEM_RECT_SELECTED,
    stroke: COLORS.INVALID,
    fill: COLORS.INVALID,
  };

  const ItemElement = {
    name,
    prototype: 'items',
    info,
    help:
      name === 'stairs'
        ? 'Direction UP/DOWN defines whether the stairs are used to go to the upper/lower floor.\nThe orientation (arrow over the stairs) defines where the first and last step are.'
        : '',
    properties: {
      width: {
        label: 'width',
        type: 'length-measure',
        defaultValue: {
          value: defaultWidth,
          unit: 'cm',
        },
        step: MEASURE_STEP_ITEM,
      },
      length: {
        label: 'length',
        type: 'length-measure',
        defaultValue: {
          value: defaultLength,
          unit: 'cm',
        },
        step: MEASURE_STEP_ITEM,
      },
      ...additionalProperties,
    },
    render2D: (element, layer, scene) => {
      const scaledWidth = GeometryUtils.getElementWidthInPixels(element, scene.scale) - ITEM_STROKE_WIDTH;
      const scaledLength = GeometryUtils.getElementLengthInPixels(element, scene.scale) - ITEM_STROKE_WIDTH;
      const angle = element.rotation + 90;

      let textRotation = 0;
      if (Math.sin((angle * Math.PI) / 180) < 0) {
        textRotation = 180;
      }
      let style = { ...STYLE_ITEM_RECT, ...rectStyle };
      if (element.selected) {
        if (Item.isSelectedItemInValidPosition(scene)) {
          style = { ...STYLE_ITEM_RECT_SELECTED, ...rectStyle };
        } else {
          style = { ...STYLE_ITEM_RECT_SELECTED_INVALID };
        }
      }

      return (
        <g data-testid={`item-${element.type}`} transform={`translate(${-scaledWidth / 2},${-scaledLength / 2})`}>
          <rect
            data-testid={`item-${element.type}-rect`}
            role="presentation"
            key="1"
            x="0"
            y="0"
            width={scaledWidth}
            height={scaledLength}
            style={style}
          />
          <text
            key="2"
            x="0"
            y="0"
            transform={`translate(${scaledWidth / 2}, ${scaledLength / 2}) scale(1,-1) rotate(${textRotation})`}
            style={{ textAnchor: 'middle', fontSize: '11px' }}
          >
            {element.type}
          </text>
        </g>
      );
    },
  };
  return ItemElement;
};

export default ItemFactory;
