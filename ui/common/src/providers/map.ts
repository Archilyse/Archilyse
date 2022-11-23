import L, { IconOptions, LatLngTuple, LeafletEventHandlerFn, Marker } from 'leaflet';
import { GeoSearchControl, OpenStreetMapProvider } from 'leaflet-geosearch';

import 'leaflet/dist/leaflet.css';

import 'leaflet-geosearch/dist/geosearch.css';

import 'leaflet-draw/dist/leaflet.draw.js';
import 'leaflet-draw/dist/leaflet.draw.css';

import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

import { SearchArgument, SearchResult } from 'leaflet-geosearch/dist/providers/provider';
import C from '../constants';
import { GeoJsonOptions, MarkerType } from '../types';
import { ProviderRequest } from './index';

const ICON_SIZE = 36;
const BOUNDS_PADDING = 0.5; // Avoid that when fitting markers into the map, some markers end up on the edge of the map.
const SURROUNDING_TYPES = {
  BUILDINGS: 'BUILDINGS',
  EXCLUSION_AREA: 'EXCLUSION_AREA',
};
const svgIconOutlined = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill='white' width="inherit" height="inherit">
  <path d="M0 0h24v24H0z" fill="none"/>
  <path stroke='${C.COLORS.PRIMARY}' d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
</svg>
`;

const svgIconFilled = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill='${C.COLORS.PRIMARY}' width="inherit" height="inherit">
  <path d="M0 0h24v24H0z" fill="none"/>
  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
</svg>
`;

const LAS_CANTERAS: LatLngTuple = [28.1390149, -15.4424323];
const mapboxApiToken = process.env.MAPBOX_TILES_TOKEN;
const TILES_URL = `https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=${mapboxApiToken}`;

type MarkerEventsType = {
  [eventName: string]: LeafletEventHandlerFn;
};

type LocationEvent = any;
type DrawEvent = any;

type MapOptionsType = {
  center?: LatLngTuple;
  zoom?: number;
  minZoom?: number;
  maxZoom?: number;
  searchOptions?: {
    search?: boolean;
    onLocationSelected?: (event: LocationEvent) => void;
  };
  drawOptions?: {
    draw?: boolean;
    onDrawCreated?: (event: DrawEvent) => void;
    onDrawEdited?: (event: DrawEvent) => void;
    onDrawDeleted?: (event: DrawEvent) => void;
  };
  geojsonOptions?: GeoJsonOptions;
};
const MAX_NATIVE_ZOOM = 19;
const DEFAULT_OPTIONS: MapOptionsType = {
  center: LAS_CANTERAS,
  zoom: 13,
  minZoom: 11,
  maxZoom: 20,
};

const setOrder = (layer, surrType) => {
  //Always put exclusion aras to the back
  if (surrType === SURROUNDING_TYPES.EXCLUSION_AREA) layer.bringToBack();
  else layer.bringToFront();
};

const getStyle = surrType => {
  switch (surrType) {
    case SURROUNDING_TYPES.BUILDINGS:
      return { color: C.GEOJSON_MAP_BUILDING_COLOR };
    case SURROUNDING_TYPES.EXCLUSION_AREA:
      return { color: C.GEOJSON_MAP_EXCLUSION_AREA_COLOR, opacity: 0.3, fillOpacity: 0.05 };
  }
};

const getPopupContent = (surrType, heightValue) => {
  let popupContent = `<form> Type: <br><select name="type" id="input_type">`;
  for (const key in SURROUNDING_TYPES)
    popupContent += `<option ${surrType == key ? 'selected' : ''} value="${key}" > ${key} </option>`;

  popupContent += `</select><br> <label id="input_height_label">Height (m)</label> <br>
                   <input id="input_height" type="number" min=0 max= 200 step="0.1" value="${heightValue}" </form>`;
  return popupContent;
};
const createGeoJSONLayer = (geojson, map) => {
  const newLayer = L.geoJSON(geojson, { style: getStyle(geojson.properties?.surrounding_type), pmIgnore: false });
  const surrType = geojson.properties?.surrounding_type || SURROUNDING_TYPES.BUILDINGS;
  const heightValue = geojson.properties?.height || 0;

  setOrder(newLayer, surrType);
  newLayer.bindPopup(getPopupContent(surrType, heightValue));

  newLayer.on('popupopen', e => {
    const _layer = e.propagatedFrom.toGeoJSON();
    const surrType = _layer.properties?.surrounding_type;
    (document.getElementById('input_type') as HTMLInputElement).value = surrType;

    if (surrType == SURROUNDING_TYPES.BUILDINGS)
      (document.getElementById('input_height') as HTMLInputElement).value = _layer.properties?.height;
    else {
      //hide input_height if it's not a building
      document.getElementById('input_height').style.display = 'none';
      document.getElementById('input_height_label').style.display = 'none';
    }
  });

  newLayer.on('popupclose', e => {
    const newSurrType = (document.getElementById('input_type') as HTMLInputElement).value;
    e.propagatedFrom.feature.properties.surrounding_type = newSurrType;
    if (newSurrType != SURROUNDING_TYPES.BUILDINGS) {
      delete e.propagatedFrom.feature.properties.height;
      (document.getElementById('input_height') as HTMLInputElement).value = '0';
    } else {
      e.propagatedFrom.feature.properties.height = (document.getElementById('input_height') as HTMLInputElement).value;
    }
    e.propagatedFrom.setStyle(getStyle(e.propagatedFrom.feature.properties.surrounding_type));
    setOrder(e.propagatedFrom, surrType);
  });

  L.PM.reInitLayer(newLayer);
  map.addLayer(newLayer);
};

const findMarker = (markers: Marker[], marker: MarkerType) => {
  const [lat, lon] = marker.coords;
  return markers.find(marker => {
    const { lat: markerLat, lng } = marker.getLatLng();
    return markerLat === lat && lng === lon;
  });
};

const getPopup = ({ versions = 0, name }) => {
  if (versions > 0) {
    return `<div><h3>${name}</h3><p>${versions} version${versions > 1 ? 's' : ''}</p><div>`;
  }
  return `<div><h3>${name}</h3>`;
};

const filledUrl = encodeURI(`data:image/svg+xml,${svgIconFilled}`).replace('#', '%23');
const outLinedUrl = encodeURI(`data:image/svg+xml,${svgIconOutlined}`).replace('#', '%23');

const commonIconOptions: Omit<IconOptions, 'iconUrl'> = {
  iconSize: [ICON_SIZE, ICON_SIZE],
  shadowSize: [0, 0],
  shadowAnchor: [0, 0],
  iconAnchor: [ICON_SIZE / 2, ICON_SIZE],
  popupAnchor: [0, -(ICON_SIZE + 2)],
};

const highlightedIcon = L.icon({
  iconUrl: filledUrl,
  className: 'highlighted-icon',
  ...commonIconOptions,
});

const regularIcon = L.icon({
  iconUrl: outLinedUrl,
  className: 'regular-icon',
  ...commonIconOptions,
});

class LocationIQProvider extends OpenStreetMapProvider {
  constructor() {
    // endpoints are updated compared to the locationIQProvider defined in leaflet-geosearch
    super({
      params: { key: process.env.LOCATION_IQ_TOKEN },
      searchUrl: 'https://eu1.locationiq.com/v1/search.php',
      reverseUrl: 'https://eu1.locationiq.com/v1/reverse.php',
    });
  }

  // Overriding it as the search of the provider doesn't handle the errors (not found, crashes...)
  async search(options: SearchArgument): Promise<SearchResult[]> {
    try {
      return super.search(options);
    } catch (error) {
      console.log(`Error searching: ${error}`);
      return [];
    }
  }
}

class Map {
  map: any = {};
  markers: Marker[] = [];
  selectedMarker: any = undefined;

  constructor() {
    this.map = {};
    this.markers = [];
    this.selectedMarker = undefined;
  }

  getInternalMapInstance() {
    return this.map;
  }

  init(mapId: string, options: MapOptionsType = {}) {
    this.map = L.map(mapId, { ...DEFAULT_OPTIONS, ...options });
    L.tileLayer(TILES_URL, {
      maxNativeZoom: MAX_NATIVE_ZOOM,
      maxZoom: options.maxZoom || DEFAULT_OPTIONS.maxZoom,
    }).addTo(this.map);
    if (options.searchOptions?.search) this.initSearchControl(options.searchOptions);
    if (options.drawOptions?.draw) this.initDrawControl(options.drawOptions);
    if (options.geojsonOptions?.draw) this.initGeojsonControl(options.geojsonOptions);
  }

  initSearchControl({ onLocationSelected = event => {} }): void {
    const provider = new LocationIQProvider();
    const searchControl = new (GeoSearchControl as any)({
      style: 'bar',
      provider: provider,
      showMarker: false, // Not being shown properly, disabled for now
      classNames: { input: 'map-search-input' },
    });
    this.map.addControl(searchControl);
    this.map.attributionControl.addAttribution(
      // Needed as per locationIQ free tier
      '<a href="https://locationiq.com/">Search powered by LocationIQ.com</a>'
    );
    this.map.on('geosearch/showlocation', onLocationSelected);
  }

  initDrawControl({ onDrawCreated = event => {}, onDrawEdited = event => {}, onDrawDeleted = event => {} }): void {
    // we ingore types here because leaflet-draw doesn't have it but TS throws an errors

    // override tooltips
    // @ts-ignore
    L.drawLocal.draw.handlers.rectangle.tooltip.start = null;
    // @ts-ignore
    L.drawLocal.draw.handlers.marker.tooltip.start = null;

    const editableLayers = new L.FeatureGroup();
    this.map.addLayer(editableLayers);

    const drawOptions = {
      position: 'topright',
      draw: {
        rectangle: {
          shapeOptions: {
            clickable: true,
          },
        },
        marker: false,
        polyline: false,
        polygon: false,
        circle: false,
        circlemarker: false,
      },
      edit: {
        featureGroup: editableLayers,
        remove: true,
      },
    };

    // @ts-ignore
    const drawControl = new L.Control.Draw(drawOptions);
    this.map.addControl(drawControl);

    // @ts-ignore
    this.map.on(L.Draw.Event.CREATED, event => {
      editableLayers.addLayer(event.layer);

      onDrawCreated(event);
    });

    // @ts-ignore
    this.map.on(L.Draw.Event.EDITED, event => {
      onDrawEdited(event);
    });

    // @ts-ignore
    this.map.on(L.Draw.Event.DELETED, event => {
      onDrawDeleted(event);
    });
  }

  initGeojsonControl(options): void {
    // add Leaflet-Geoman controls with some options to the map
    this.map.pm.addControls({
      position: 'topleft',
      drawCircle: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawMarker: false,
      drawRectangle: false,
      cutPolygon: false,
    });
    if (options.sitePlans) {
      L.geoJSON(options.sitePlans, {
        style: { color: C.GEOJSON_MAP_SITE_COLOR, fillOpacity: 0.05, opacity: 0.3 },
        pmIgnore: true,
      }).addTo(this.map);
    }

    options.initialGeoJson?.features.forEach(geojson => createGeoJSONLayer(geojson, this.map));

    //Save button
    this.map.pm.Toolbar.createCustomControl({
      name: 'Save',
      block: 'custom',
      className: 'leaflet-pm-icon-save',
      title: 'Save manual polygons',
      onClick: async () => {
        const layers = (L.PM.Utils.findLayers(this.map) as unknown) as L.GeoJSON[];
        try {
          await ProviderRequest.put(C.ENDPOINTS.MANUAL_SURROUNDINGS(options.siteID), {
            type: 'FeatureCollection',
            features: layers.map(x => x.toGeoJSON()),
          });
          options.onSaved();
        } catch (e) {
          options.onError();
        }
      },
    });

    //Legend
    // @ts-ignore
    const legend = L.control({ position: 'topright' });
    legend.onAdd = function (map) {
      const div = L.DomUtil.create('div', 'info legend');
      div.innerHTML += '<strong>Categories</strong>';

      for (const surrType in SURROUNDING_TYPES)
        div.innerHTML += `<br><i style="background:${getStyle(surrType).color}"></i>${surrType}`;

      div.innerHTML += `<br><i style="background:${C.GEOJSON_MAP_SITE_COLOR}"></i>SITE`;
      return div;
    };

    legend.addTo(this.map);

    this.map.on('pm:create', e => {
      const geojson = e.layer.toGeoJSON();
      //Delete layer and creates a new one
      e.target.removeLayer(e.layer);
      geojson.properties = { surrounding_type: SURROUNDING_TYPES.BUILDINGS, height: 0 };
      createGeoJSONLayer(geojson, this.map);
    });
  }

  clearSelectedMarker() {
    this.selectedMarker && this.selectedMarker.setIcon(regularIcon);
  }

  selectMarker(marker: MarkerType) {
    this.clearSelectedMarker();

    const selectedMarker = findMarker(this.markers, marker);
    if (!selectedMarker) return;

    selectedMarker.setIcon(highlightedIcon);
    this.selectedMarker = selectedMarker;
  }

  addMarkers(markers: MarkerType[], events: MarkerEventsType = {}) {
    markers.forEach(m => {
      const hasThisMarker = findMarker(this.markers, m);
      if (hasThisMarker) return null;

      const marker = L.marker(m.coords, { icon: regularIcon });
      Object.entries(events).forEach(([eventName, handler = () => {}]) => {
        marker.on(eventName, handler);
        marker.on('mouseover', () => {
          marker.openPopup();
          marker.setIcon(highlightedIcon);
        });
        marker.on('mouseout', () => {
          marker.closePopup();
          marker.setIcon(regularIcon);
        });
      });
      marker.bindPopup(getPopup(m.details));
      marker.addTo(this.map);
      this.markers.push(marker);
    });
  }

  centerAroundMarkers(markers: MarkerType[]) {
    const coords = markers.map(m => m.coords);
    const bounds = L.latLngBounds(coords).pad(BOUNDS_PADDING);
    this.map.fitBounds(bounds);
  }

  removeMarkers() {
    this.markers.forEach(marker => {
      this.map.removeLayer(marker);
    });
    this.markers = [];
  }

  remove() {
    this.map.remove();
  }
}

export default Map;
