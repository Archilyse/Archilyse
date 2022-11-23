import React, { useEffect, useState } from 'react';
import { MapView } from '@here/harp-mapview';
import HarpMapViewRenderer from '../libs/HarpMapViewRenderer';
import HeatmapCameraControls from '../libs/HeatmatCameraControls';
import { SIMULATION_MODE } from '../../../types';
import { DataSource } from '../../SimulationViewer/libs/DataSource';

export type HeatmapHarpMapControls = { map: MapView; camera: HeatmapCameraControls };

type Props = {
  canvas: React.MutableRefObject<HTMLCanvasElement>;
  showMap: boolean;
  dataSource?: SIMULATION_MODE;
  backgroundColor?: number;
};

const useHarpMap = ({ canvas, showMap, dataSource, backgroundColor }: Props): HeatmapHarpMapControls => {
  const [state, setState] = useState<HeatmapHarpMapControls>({ map: null, camera: null });

  useEffect(() => {
    const [map, camera] = HarpMapViewRenderer.initMapView(canvas.current, { dataSource, backgroundColor });

    setState({ map, camera });

    return HarpMapViewRenderer.setUpEvents(canvas.current, { map, camera }, showMap);
  }, []);

  useEffect(() => {
    if (state.map) DataSource.setUpDataSource(state.map, dataSource);
  }, [dataSource]);

  return state;
};

export default useHarpMap;
