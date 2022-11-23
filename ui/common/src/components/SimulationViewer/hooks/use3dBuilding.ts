import { useEffect, useState } from 'react';
import { decode } from '@msgpack/msgpack';
import { ProviderRequest } from '../../../providers';
import { addUnits, removePreviousBuildings } from '../libs/UnitRenderer';
import C from '../../../constants';
import { SINGLE_UNIT_CAM_DISTANCE } from '../libs/SimConstants';
import { usePrevious } from '../../../hooks';
import { cleanThreeJSAnnotations } from '../libs/AnnotationsRenderer';
import { ThreeDUnit } from '../../../types';

const { ENDPOINTS } = C;

type Use3dBuildingResult = {
  loadingStatus: { addedToMap: boolean; loading: boolean };
  error: string;
};

// Asynchronously decode byte response to avoid blocking UI as it can take a while
const decodeByteResponse = async unitCoordinatesEncoded => {
  const unitCoordinates = decode(unitCoordinatesEncoded) as ThreeDUnit[];
  return unitCoordinates;
};

const use3dBuilding = ({ mapControls, buildingId, context3dUnits }): Use3dBuildingResult => {
  const [elevation, setElevation] = useState(undefined);
  const [unitCoordinates, setUnitCoordinates] = useState([]);
  const [loadingStatus, setLoadingStatus] = useState({ addedToMap: false, loading: false });
  const [error, setError] = useState('');

  const previousContext3dUnits = usePrevious(context3dUnits);

  const fetchBuilding = async buildingId => {
    try {
      const requests = [
        ProviderRequest.getCached(ENDPOINTS.BUILDING(buildingId)),
        ProviderRequest.getCached(ENDPOINTS.BUILDING_3D(buildingId), { responseType: 'arraybuffer' }),
      ];
      const [{ elevation }, unitCoordinatesEncoded] = await Promise.all(requests);
      const unitCoordinates = await decodeByteResponse(unitCoordinatesEncoded);
      setElevation(elevation);
      setUnitCoordinates(unitCoordinates);

      setLoadingStatus({ addedToMap: false, loading: false });
    } catch (error) {
      setError('Unexpected error loading the building');
      console.error('Error fetching building in 3d', error);
    }
  };

  const load3dBuildingInTheMap = async (mapControls, context3dUnits) => {
    context3dUnits = context3dUnits || [];
    try {
      setLoadingStatus({ addedToMap: false, loading: true });

      removePreviousBuildings(mapControls.map);
      const foundUnit = unitCoordinates.find(([unitClientId], _coords) => unitClientId === context3dUnits[0]);
      if (!foundUnit && context3dUnits.length > 0) return;
      const { camPosition, camExtraDistance } = await addUnits(
        mapControls.map,
        mapControls.unit.unitToMeshes,
        unitCoordinates,
        context3dUnits,
        elevation
      );
      const displaySingleUnit = context3dUnits.length === 1;
      mapControls.camera.reset();
      mapControls.camera.setPosition(camPosition);
      if (displaySingleUnit) {
        mapControls.camera.setDistance(SINGLE_UNIT_CAM_DISTANCE);
      } else {
        mapControls.camera.changeDistance(camExtraDistance);
      }
      mapControls.camera.cameraSetUp();
      mapControls.map.update();

      setLoadingStatus({ addedToMap: true, loading: false });
    } catch (error) {
      setError('Unexpected error loading the building');
      console.error('Error loading the 3d building in the map', error);
    }
  };

  useEffect(() => {
    if (!buildingId || !mapControls.map) return;

    fetchBuilding(buildingId);
  }, [mapControls, buildingId]);

  useEffect(() => {
    if (!unitCoordinates || !unitCoordinates.length || !mapControls || !mapControls.map) return;

    const notLoadedInMap = !loadingStatus.addedToMap && !loadingStatus.loading;
    const hasNewUnits =
      context3dUnits?.length !== previousContext3dUnits?.length &&
      context3dUnits.some(unit => !previousContext3dUnits.includes(unit));

    if (notLoadedInMap || hasNewUnits) {
      load3dBuildingInTheMap(mapControls, context3dUnits);
    }
  }, [mapControls, context3dUnits, unitCoordinates, loadingStatus]);

  useEffect(() => {
    return () => {
      if (mapControls?.map) {
        cleanThreeJSAnnotations(mapControls.map);
      }
    };
  }, []);

  return { loadingStatus, error };
};

export default use3dBuilding;
