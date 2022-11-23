import { useEffect, useState } from 'react';
import { SVG_PLAN_CLASSNAME } from '../constants';

export const getCurrentZoomLvl = () => {
  const elementWithMatrixTransform = document.querySelector(`.${SVG_PLAN_CLASSNAME} svg > g`);
  const newMatrixTransform = (elementWithMatrixTransform as HTMLElement).getAttribute('transform') as string;
  const matrixValues = newMatrixTransform
    .slice(7, -1)
    .split(',')
    .map(v => Number(v));
  const zoom = matrixValues[0]; //a
  return zoom;
};

export const useSvgPlanTransforms = (): any => {
  const [svgTransforms, setSvgTransforms] = useState({
    zoom: 1,
    transformX: 0,
    transformY: 0,
  });

  useEffect(() => {
    const elementWithMatrixTransform = document.querySelector(`.${SVG_PLAN_CLASSNAME} svg > g`);
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'transform') {
          const newMatrixTransform = (mutation.target as HTMLElement).getAttribute('transform') as string;
          const matrixValues = newMatrixTransform
            .slice(7, -1)
            .split(',')
            .map(v => Number(v));
          const zoom = matrixValues[0]; //a
          const transformX = matrixValues[4]; // e
          const transformY = matrixValues[5]; // f
          setSvgTransforms({
            zoom,
            transformX,
            transformY,
          });
        }
      });
    });
    observer.observe(elementWithMatrixTransform, {
      attributes: true, //configure it to listen to attribute changes
    });

    return () => {
      observer.disconnect();
    };
  }, []);

  return svgTransforms;
};
