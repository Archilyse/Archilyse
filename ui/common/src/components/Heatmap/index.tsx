import React, { useRef } from 'react';
import cn from 'classnames';
import C from '../../constants';
import { RequestStatus, SIMULATION_MODE, SIMULATION_TYPES } from '../../types';
import LoadingIndicator from '../LoadingIndicator';
import useBrooks from './hooks/useBrooks';
import useHarpMap from './hooks/useHarpMap';
import useHeatmap from './hooks/useHeatmap';
import StatisticsInfo from './components/StatisticsInfo';
import './heatmap.scss';

export type HeatmapProps = {
  id?: string;
  planId?: number;
  siteId?: number;
  unitIds: number[];
  simulationName: string;
  displayInfo?: boolean;
  infoSize?: 'medium' | 'small';
  rotationToNorth?: number;
  heatmapEndpoint?: (...args) => string;
  hexagonRadius?: number;
  showBrooks?: boolean;
  showMap?: boolean;
  mapSimulationMode?: SIMULATION_MODE;
  backgroundColor?: number;
};

const getHeatmapTypeBySimulationName = (simulationName: string) => {
  return simulationName.includes(SIMULATION_TYPES.CONNECTIVITY)
    ? SIMULATION_TYPES.CONNECTIVITY
    : SIMULATION_TYPES.VIEW_SUN;
};

/**
 * If `simulationName` will change frequently, provide `planId` and `unitIds` wrapped in useMemo/useCallback
 * for better performance
 */
const Heatmap = ({
  id,
  planId,
  siteId = undefined,
  unitIds,
  simulationName,
  displayInfo = true,
  infoSize = 'medium',
  rotationToNorth,
  heatmapEndpoint = C.ENDPOINTS.UNIT_HEATMAPS,
  showMap = false,
  showBrooks = true,
  hexagonRadius,
  mapSimulationMode,
  backgroundColor,
}: HeatmapProps): JSX.Element => {
  const canvas = useRef<HTMLCanvasElement>();

  const mapControls = useHarpMap({ canvas, showMap, dataSource: mapSimulationMode, backgroundColor });

  const { brooks } = useBrooks({
    planId,
    unitIds,
    mapControls,
    heatmapType: getHeatmapTypeBySimulationName(simulationName),
    showBrooks,
  });

  const { heatmap, statistics } = useHeatmap({
    siteId,
    unitIds,
    simulationName,
    mapControls,
    rotationToNorth,
    endpoint: heatmapEndpoint,
    hexagonRadius,
    showMap,
  });

  const isFullyLoading = brooks.status === RequestStatus.PENDING && heatmap.status === RequestStatus.PENDING;
  const isPartiallyLoading =
    (brooks.status === RequestStatus.PENDING && heatmap.status !== RequestStatus.PENDING) ||
    (brooks.status !== RequestStatus.PENDING && heatmap.status === RequestStatus.PENDING);

  return (
    <div id={id} className="heatmap-canvas-container">
      {(isFullyLoading || isPartiallyLoading) && (
        <LoadingIndicator className={cn({ fully: isFullyLoading, partially: isPartiallyLoading })} />
      )}
      {displayInfo && statistics && (
        <StatisticsInfo statistics={statistics} simulationName={simulationName} size={infoSize} />
      )}
      <canvas ref={canvas} tabIndex={1} />
    </div>
  );
};

/**
 * Prevents re-renders only when `simulationName` static but `unitIds` changes frequently
 */
const hasChanged = (prevProps: HeatmapProps, nextProps: HeatmapProps) => {
  const { unitIds: prevUnitIds } = prevProps;
  const { unitIds: nextUnitIds } = nextProps;

  let areUnitIdsEqual = true;
  if (prevUnitIds && nextUnitIds) {
    if (nextUnitIds.length !== prevUnitIds.length) areUnitIdsEqual = false;

    areUnitIdsEqual = nextUnitIds.every((unitId, index) => unitId === prevUnitIds[index]);
  }

  return (
    areUnitIdsEqual &&
    prevProps.planId === nextProps.planId &&
    prevProps.simulationName === nextProps.simulationName &&
    prevProps.displayInfo === nextProps.displayInfo &&
    prevProps.rotationToNorth === nextProps.rotationToNorth &&
    prevProps.mapSimulationMode === nextProps.mapSimulationMode
  );
};

export default React.memo(Heatmap, hasChanged);
