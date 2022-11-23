import React, { useEffect, useState } from 'react';
import { createRequestState, Map, MarkerType, RequestStatus } from 'archilyse-ui-components';
import { C } from 'Common';
import { ProviderRequest } from 'Providers';
import { PotentialSimulation } from 'Common/types';
import Can from 'Components/Can';
import { checkAccess } from 'Common/roles';
import SimulationsList from './components/SimulationsList';
import { RequestFormFields } from './components/RequestForm';
import './home.scss';

const createMarkersFromCoords = ([lat, lon]: [number, number]): MarkerType[] => {
  return [
    {
      details: {
        name: `${lat}, ${lon}`,
      },
      coords: [lat, lon],
    },
  ];
};

const findCoordsBox = latLngs => {
  const lats = latLngs.map(({ lat }) => lat);
  const lngs = latLngs.map(({ lng }) => lng);

  const [maxLat, minLat] = [Math.max(...lats), Math.min(...lats)];
  const [maxLng, minLng] = [Math.max(...lngs), Math.min(...lngs)];

  return [maxLat, minLat, maxLng, minLng];
};

const serializeLatLngsBox = (maxLat, minLat, maxLng, minLng) => ({
  max_lat: maxLat,
  min_lat: minLat,
  max_lon: maxLng,
  min_lon: minLng,
});

const initialFields: RequestFormFields = {
  latitude: null,
  longitude: null,
  floor: null,
  simType: 'sun',
} as const;

const Home = () => {
  const [simulations, dispatchSimulations] = useState(createRequestState([] as PotentialSimulation[]));
  const [fields, setFields] = useState(initialFields);

  const handleLocationSelected = (event): void => {
    const { x: lon, y: lat } = event.location;
    setFields(_fields => ({ ..._fields, latitude: lat, longitude: lon }));
  };

  const handleDrawCreated = (event): void => {
    try {
      const [maxLat, minLat, maxLng, minLng] = findCoordsBox(event.layer._latlngs[0]);

      fetchSimulations(serializeLatLngsBox(maxLat, minLat, maxLng, minLng));
    } catch (error) {
      console.error('Error occurred while creating a draw', error);
    }
  };

  const handleDrawEdited = (event): void => {
    try {
      const [layer]: any = Object.values(event.layers._layers);
      const [maxLat, minLat, maxLng, minLng] = findCoordsBox(layer._latlngs[0]);

      fetchSimulations(serializeLatLngsBox(maxLat, minLat, maxLng, minLng));
    } catch (error) {
      console.error('Error occurred while editing a draw', error);
    }
  };

  const handleDrawDeleted = (): void => {
    try {
      fetchSimulations();
    } catch (error) {
      console.error('Error ouccured while deleting a draw', error);
    }
  };

  const fetchSimulations = async (latLngBox = null) => {
    dispatchSimulations({ ...simulations, status: RequestStatus.PENDING, error: null });

    try {
      const result = await ProviderRequest.get(C.ENDPOINTS.SIMULATIONS_LIST(), latLngBox);

      dispatchSimulations({ data: result, status: RequestStatus.FULFILLED, error: null });
    } catch (error) {
      const message =
        error.response?.data.message || error.response?.data.msg || 'Error occured while loading simulations';
      dispatchSimulations({ ...simulations, status: RequestStatus.REJECTED, error: message });
    }
  };

  useEffect(() => {
    if (checkAccess('simulations-list')) fetchSimulations();
  }, []);

  const { latitude: lat, longitude: lon } = fields;
  const markers = lat && lon ? createMarkersFromCoords([lat, lon]) : [];

  return (
    <main id="potential-view-home" className="home-container">
      <div className="content-container">
        <h2 className="home-heading">Potential Simulations</h2>

        <Can perform="simulations-list" yes={() => <SimulationsList simulations={simulations} />} />
      </div>
      <div className="map-container">
        <Map
          markers={markers}
          searchOptions={{
            search: true,
            onLocationSelected: handleLocationSelected,
          }}
          drawOptions={{
            draw: true,
            onDrawCreated: handleDrawCreated,
            onDrawEdited: handleDrawEdited,
            onDrawDeleted: handleDrawDeleted,
          }}
        />
      </div>
    </main>
  );
};

export default Home;
