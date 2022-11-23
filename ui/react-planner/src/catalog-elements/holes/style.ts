import { CATALOG_ELEMENT_OPACITY, CATALOG_ELEMENT_OPACITY_SELECTED, COLORS } from '../../constants';

export const PADDING = 6;

export const STYLE_HOLE_BASE = {
  stroke: COLORS.CATALOG.DOOR,
  fill: COLORS.CATALOG.DOOR,
  strokeWidth: `${PADDING}px`,
  opacity: CATALOG_ELEMENT_OPACITY,
};
export const STYLE_HOLE_SELECTED = {
  stroke: COLORS.SELECTED_ELEMENT,
  strokeWidth: `${PADDING}px`,
  fill: COLORS.SELECTED_ELEMENT,
  cursor: 'move',
  opacity: CATALOG_ELEMENT_OPACITY_SELECTED,
};
export const STYLE_ARC_BASE = {
  stroke: COLORS.CATALOG.DOOR,
  strokeWidth: `${PADDING}px`,
  strokeDasharray: '5,5',
  fill: 'none',
  opacity: CATALOG_ELEMENT_OPACITY,
};
export const STYLE_ARC_SELECTED = {
  stroke: COLORS.SELECTED_ELEMENT,
  strokeWidth: `${PADDING}px`,
  strokeDasharray: '5,5',
  fill: 'none',
  cursor: 'move',
  opacity: CATALOG_ELEMENT_OPACITY_SELECTED,
};
export const STYLE_HOLE_BASE_ENTRANCE_DOOR = {
  ...STYLE_HOLE_BASE,
  strokeWidth: `${PADDING}px`,
  stroke: COLORS.CATALOG.ENTRANCE_DOOR,
  fill: COLORS.CATALOG.ENTRANCE_DOOR,
};
export const STYLE_ARC_ENTRANCE_DOOR = {
  ...STYLE_ARC_BASE,
  stroke: COLORS.CATALOG.ENTRANCE_DOOR,
};
export const STYLE_WINDOW_BASE = {
  ...STYLE_HOLE_BASE,
  stroke: COLORS.CATALOG.WINDOW,
  strokeWidth: '0px',
  fill: COLORS.CATALOG.WINDOW,
};
export const STYLE_WINDOW_SELECTED = {
  ...STYLE_HOLE_SELECTED,
  strokeWidth: '0px',
};
export const STYLE_SLIDING_DOOR = {
  ...STYLE_HOLE_BASE,
  strokeWidth: '0px',
};
export const STYLE_SLIDING_DOOR_SELECTED = {
  ...STYLE_HOLE_SELECTED,
  strokeWidth: '0px',
};

export const ENTRANCE_DOOR_STYLE = (selected: boolean) => {
  return selected
    ? {
        base: STYLE_HOLE_SELECTED,
        arc: STYLE_ARC_SELECTED,
        polygon: { ...STYLE_HOLE_SELECTED, strokeWidth: '0px' },
      }
    : {
        base: STYLE_HOLE_BASE_ENTRANCE_DOOR,
        arc: STYLE_ARC_ENTRANCE_DOOR,
        polygon: { ...STYLE_HOLE_BASE_ENTRANCE_DOOR, strokeWidth: '0px' },
      };
};

export const DOOR_STYLE = (selected: boolean) => {
  const style = selected
    ? {
        base: STYLE_HOLE_SELECTED,
        arc: STYLE_ARC_SELECTED,
        polygon: { ...STYLE_HOLE_SELECTED, strokeWidth: '0px' },
      }
    : {
        base: STYLE_HOLE_BASE,
        arc: STYLE_ARC_BASE,
        polygon: { ...STYLE_HOLE_BASE, strokeWidth: '0px' },
      };
  return style;
};
