import React from 'react';
import { Map, MarkerType } from 'archilyse-ui-components';

const getLocationMarker = (coordinates): MarkerType[] => {
  return coordinates.lat && coordinates.lon
    ? [
        {
          details: {
            name: `${coordinates.lat}, ${coordinates.lon}`,
          },
          coords: [coordinates.lat, coordinates.lon],
        },
      ]
    : undefined;
};

const SiteMap = ({ onMapLocationSelected, coordinates = undefined }) => {
  const onLocationSelected = event => {
    const { x: lon, y: lat } = event.location;
    onMapLocationSelected({ lat, lon });
  };
  const markers = getLocationMarker(coordinates);
  return (
    <div className="site-map">
      <Map
        searchOptions={{
          search: true,
          onLocationSelected,
        }}
        markers={markers}
      />
    </div>
  );
};

export default SiteMap;
