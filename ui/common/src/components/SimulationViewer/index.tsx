import React, { useEffect, useRef } from 'react';
import LoadingIndicator from '../LoadingIndicator';
import { SimulationViewerProps } from '../../types';
import { colorizeUnitsByPrice, highlightUnits } from './libs/UnitRenderer';
import './simulationViewer.scss';
import { use3dBuilding, use3dMap } from './hooks';

const SimulationViewer = ({
  buildingId = null,
  simType,
  context3dUnits = null,
  highlighted3dUnits = [],
  currentUnits = [],
  colorizeByPrice = false,
}: SimulationViewerProps): JSX.Element => {
  const canvasRef = useRef(null);
  const mapRef = useRef(null);

  const { loaded: mapLoaded, mapControls, error: mapError } = use3dMap({ canvasRef, mapRef, simType });
  const { loadingStatus: buildingStatus, error: buildingError } = use3dBuilding({
    buildingId,
    context3dUnits,
    mapControls,
  });

  useEffect(() => {
    if (!mapControls.map || !buildingStatus.addedToMap || !mapControls.unit?.unitToMeshes) return;
    if (currentUnits.length > 0 && colorizeByPrice) {
      colorizeUnitsByPrice({ mapControls, currentUnits });
    }
  }, [mapControls, buildingStatus, currentUnits, colorizeByPrice]);

  useEffect(() => {
    if (!mapControls.map || !buildingStatus.addedToMap || !mapControls.unit?.unitToMeshes) return;
    highlightUnits({ mapControls, highlighted3dUnits, currentUnits, context3dUnits, colorizeByPrice });
  }, [mapControls, buildingStatus, currentUnits, highlighted3dUnits, context3dUnits]);

  const isFetching = !buildingStatus.addedToMap && buildingId;

  return (
    <div className="simulationViewer">
      {isFetching && !buildingError && (
        <div className="loading">
          <LoadingIndicator />
        </div>
      )}
      {buildingError && <div className="error">{buildingError}</div>}
      {mapError && <div className="error">{mapError}</div>}
      <canvas id={mapLoaded ? '3d-canvas' : ''} ref={canvasRef} tabIndex={1} />
    </div>
  );
};

export default SimulationViewer;
