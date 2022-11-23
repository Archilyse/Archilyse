import React, { useContext } from 'react';
import { Map, SnackbarContext } from 'archilyse-ui-components';
import './editorMap.scss';

const EditorMap = ({ coordinates, surrGeoJson, sitePlans, siteID }) => {
  const snackbar = useContext(SnackbarContext);
  return (
    <div className="editor-map">
      <Map
        center={coordinates}
        initialZoom={19}
        geojsonOptions={{
          draw: true,
          initialGeoJson: surrGeoJson,
          sitePlans: sitePlans,
          siteID: siteID,
          onSaved: () => {
            snackbar.show({ message: 'Polygons saved successfully', severity: 'success' });
          },
          onError: () => {
            snackbar.show({ message: 'Failed to save manual polygons', severity: 'error' });
          },
        }}
      />
    </div>
  );
};
export default EditorMap;
