import { LatLngTuple } from 'leaflet';
import React, { useEffect, useState } from 'react';
import { usePrevious } from '../../hooks';
import { ProviderMap } from '../../providers';
import { GeoJsonOptions, MarkerType } from '../../types';
import './map.scss';

const MAP_ID = 'map';

const ZURICH: LatLngTuple = [47.3774337, 8.4666757];
const INITIAL_ZOOM = 13;

const areMarkersTheSame = (currentMarkers, previousMarkers) => {
  const currentCoords = currentMarkers?.map(marker => marker.coords.join(','));
  const previousCoords = previousMarkers?.map(marker => marker.coords.join(','));
  const sameMarkers =
    currentCoords?.length === previousCoords?.length && currentCoords.every(coord => previousCoords.includes(coord));
  return sameMarkers;
};

const addMarkersToMap = (map, markers, handlers) => {
  if (!markers || !markers.length) return;
  const { onMouseOutMarker, onMouseOverMarker, onClickMarker } = handlers;
  map.removeMarkers();
  map.addMarkers(markers, { mouseout: onMouseOutMarker, mouseover: onMouseOverMarker, click: onClickMarker });
  map.centerAroundMarkers(markers);
};

type Props = {
  center?: LatLngTuple;
  initialZoom?: number;
  markers?: MarkerType[];
  selectedMarker?: MarkerType;
  onClickMarker?: (...args) => void;
  onMouseOverMarker?: (...args) => void;
  onMouseOutMarker?: (...args) => void;
  searchOptions?: {
    search?: boolean;
    onLocationSelected?: (...args) => void;
  };
  drawOptions?: {
    draw?: boolean;
    onDrawCreated?: (...args) => void;
    onDrawEdited?: (...args) => void;
    onDrawDeleted?: (...args) => void;
  };
  geojsonOptions?: GeoJsonOptions;
};

const Map = ({
  center = ZURICH,
  initialZoom = INITIAL_ZOOM,
  markers = [],
  selectedMarker = null,
  onClickMarker = undefined,
  onMouseOverMarker = undefined,
  onMouseOutMarker = undefined,
  searchOptions = { search: false, onLocationSelected: undefined },
  drawOptions = { draw: false, onDrawCreated: undefined, onDrawEdited: undefined, onDrawDeleted: undefined },
  geojsonOptions = { draw: false, siteID: undefined },
}: Props): JSX.Element => {
  const [map, setMap] = useState<ProviderMap>(undefined);
  const previousMarkers = usePrevious(markers);
  useEffect(() => {
    const map = new ProviderMap();

    map.init(MAP_ID, {
      center,
      zoom: initialZoom,
      searchOptions,
      drawOptions,
      geojsonOptions,
    });

    setMap(map);
    addMarkersToMap(map, markers, { onMouseOutMarker, onMouseOverMarker, onClickMarker });
    return () => {
      map.remove();
    };
  }, []);

  useEffect(() => {
    if (!map || !markers || !markers.length || areMarkersTheSame(markers, previousMarkers)) return;
    addMarkersToMap(map, markers, { onMouseOutMarker, onMouseOverMarker, onClickMarker });
  }, [map, markers]);

  useEffect(() => {
    if (!map) return;
    if (selectedMarker) {
      map.selectMarker(selectedMarker);
    } else {
      map.clearSelectedMarker();
    }
  }, [map, selectedMarker]);

  return <div id={MAP_ID} className={'map'}></div>;
};

export default Map;
