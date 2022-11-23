import React from 'react';
import { Map, MarkerType } from 'archilyse-ui-components';
import { DMSItem, GetSitesResponse } from 'Common/types';
import { useStore } from 'Components/DataView/hooks';
import { C } from 'Common';
import { useHistory } from 'react-router-dom';
import './viewDrawer.scss';
import { inView } from 'Components/DataView/modules';

type LeafletMarketType = {
  latlng: { lat: string; lng: string };
};

const getSelectedMarker = (hoveredItem, sites): MarkerType => {
  if (!sites) {
    return;
  }
  const foundSite = sites.find(site => site.id === hoveredItem?.id);

  if (!foundSite) {
    return;
  }
  return {
    details: {
      name: foundSite.name,
      versions: foundSite.versions,
    },
    coords: [foundSite.lat, foundSite.lon],
  };
};

const getMarkers = (sites: GetSitesResponse[]): MarkerType[] => {
  if (!sites || !sites.length) return null;

  return sites.map(site => ({
    details: { name: site.name },
    coords: [Number(site.lat), Number(site.lon)],
  }));
};

const findSiteByMarker = (sites: GetSitesResponse[], marker: LeafletMarketType): GetSitesResponse => {
  const { lat, lng: lon } = marker.latlng;
  const foundSite = sites.find(site => site.lat === lat && site.lon === lon);
  return foundSite;
};

const getVisibleSites = (sites: GetSitesResponse[], visibleItems: DMSItem[], pathname: string) => {
  const visibleSitesById = visibleItems.reduce((accum, item) => {
    if (item.type === 'folder-sites') accum[item.id] = item;
    return accum;
  }, {});

  const insideASite = inView([C.DMS_VIEWS.BUILDINGS], pathname) && sites.length === 1;
  return insideASite ? sites : sites.filter(site => visibleSitesById[site.id]);
};

const MarkersMap = ({ pathname }) => {
  const mapSites = useStore(state => state.mapSites);
  const hoveredItem = useStore(state => state.hoveredItem);
  const setHoveredItem = useStore(state => state.setHoveredItem);
  const visibleItems = useStore(state => state.visibleItems);

  const visibleSites = getVisibleSites(mapSites, visibleItems, pathname);

  const history = useHistory();
  const markers = getMarkers(visibleSites);
  const selectedMarker = getSelectedMarker(hoveredItem, visibleSites);

  const onClickMarker = marker => {
    const clickedSite = findSiteByMarker(visibleSites, marker);
    if (clickedSite) {
      history.push(C.URLS.BUILDINGS_BY_SITE(clickedSite.id));
    }
  };

  const onMouseOverMarker = marker => {
    const hoveredSite = findSiteByMarker(visibleSites, marker);
    if (hoveredSite) {
      setHoveredItem(hoveredSite);
    }
  };

  const onMouseOutMarker = () => {
    setHoveredItem(undefined);
  };

  return (
    <Map
      markers={markers}
      onClickMarker={onClickMarker}
      onMouseOverMarker={onMouseOverMarker}
      onMouseOutMarker={onMouseOutMarker}
      selectedMarker={selectedMarker}
    />
  );
};

export default MarkersMap;
