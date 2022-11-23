import React, { useLayoutEffect, useRef } from 'react';
import * as GeometryUtils from '../../utils/geometry';
import { ProviderHash } from '../../providers';
import { MODE_IDLE } from '../../constants';
import { getCurrentZoomLvl } from '../../hooks/useSvgPlanTransforms';

const SELECTED_AREA_STYLE_TEXT = {
  textAnchor: 'middle',
  fontSize: '36px',
  fontFamily: '"Courier New", Courier, monospace',
  pointerEvents: 'none',
  fontWeight: 'bold',

  //http://stackoverflow.com/questions/826782/how-to-disable-text-selection-highlighting-using-css
  WebkitTouchCallout: 'none' /* iOS Safari */,
  WebkitUserSelect: 'none' /* Chrome/Safari/Opera */,
  MozUserSelect: 'none' /* Firefox */,
  MsUserSelect: 'none' /* Internet Explorer/Edge */,
  userSelect: 'none',
};

const DEFAULT_AREA_STYLE_TEXT = { ...SELECTED_AREA_STYLE_TEXT, fontWeight: '100' };

const useAutoFontSize = textRef => {
  useLayoutEffect(() => {
    const currentZoomLvl = getCurrentZoomLvl().toFixed(3);
    const textElem = textRef.current;
    let textElemWidth = textElem.getBoundingClientRect().width;
    const areaElem = textElem.previousSibling;
    let areaElemWidth = areaElem.getBoundingClientRect().width;
    // adjust width to zoom of 1 (100%)
    if (currentZoomLvl < 1) {
      textElemWidth = textElemWidth / currentZoomLvl;
      areaElemWidth = areaElemWidth / currentZoomLvl;
    }
    // if text width is bigger than the area width
    if (textElemWidth > areaElemWidth) {
      const diff = textElemWidth - areaElemWidth;
      if (diff < 10) {
        textElem.style.fontSize = '30px';
      } else if (diff > 10 && diff < 30) {
        textElem.style.fontSize = '29px';
      } else if (diff > 30 && diff < 60) {
        textElem.style.fontSize = '21px';
      } else if (diff > 60 && diff < 80) {
        textElem.style.fontSize = '19px';
      } else if (diff > 80 && diff < 100) {
        textElem.style.fontSize = '16px';
      } else if (diff > 100 && diff < 120) {
        textElem.style.fontSize = '13px';
      } else if (diff > 120) {
        textElem.style.fontSize = '10px';
      }
    }
  }, []);
};

const AreaInfo = ({ area, planScale, scaleTool }) => {
  const textRef = useRef();
  useAutoFontSize(textRef);

  const [areaCoordinates] = area.coords;
  if (!areaCoordinates || areaCoordinates === 0) return null;

  const areaType = area.properties.areaType;
  const areaCenter = GeometryUtils.getAreaCenter(area);
  const applicableTextStyle = area.selected ? SELECTED_AREA_STYLE_TEXT : DEFAULT_AREA_STYLE_TEXT;

  const areaSizeInSqMeters =
    area.isScaleArea && scaleTool.areaSize ? scaleTool.areaSize : GeometryUtils.getAreaSizeFromScale(area, planScale);

  return (
    <>
      <text
        ref={textRef}
        x="0"
        y="0"
        transform={`translate(${areaCenter[0]} ${areaCenter[1]}) scale(1, -1)`}
        style={applicableTextStyle}
      >
        {areaSizeInSqMeters} m²
      </text>
      <text
        x="0"
        y="0"
        transform={`translate(${areaCenter[0]} ${areaCenter[1] - 50}) scale(1, -1)`}
        style={applicableTextStyle}
      >
        {areaType?.toUpperCase()}
      </text>
    </>
  );
};
const Area = ({ layer, area, catalog, mode, scale: planScale = 1, scaleTool }) => {
  const catalogElement = catalog.getElement(area.type);

  const rendered = catalogElement.render2D(area, layer, mode);

  return (
    <g
      data-testid={`viewer-area-${area.id}`}
      data-element-root
      data-prototype={area.prototype}
      data-id={area.id}
      data-selected={area.selected}
      data-layer={layer.id}
    >
      {rendered}
      <AreaInfo area={area} planScale={planScale} scaleTool={scaleTool} />
    </g>
  );
};

/**
  If this method returns false, the area will re-render.

  Notice:
  - The area is modified *after* the user is interacting, so no point in re-rendering in the meantime.
  - The slower check is the one related to the lines, and hence it is located at the end.
*/

function areEqual(prevProps, nextProps) {
  // allow rendering selected areas again, when mode is changed
  // because all selected areas will be unselected and style must change
  if (prevProps.area.selected && nextProps.mode !== MODE_IDLE) {
    return false;
  }

  if (prevProps.scaleTool.areaSize || nextProps.scaleTool.areaSize) {
    return false;
  }

  const userIsInteracting = nextProps.mode !== MODE_IDLE;
  if (userIsInteracting) return true;

  const areaHasChanged = nextProps.area !== prevProps.area;
  if (areaHasChanged) return false;

  //Allow re-rerendering area if it's selected or unselected
  if (prevProps.area.selected !== nextProps.area.selected) {
    return false;
  }

  return true;
}

export default React.memo(Area, areEqual);
