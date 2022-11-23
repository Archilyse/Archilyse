import React, { useState } from 'react';
import { LoadingIndicator, SIMULATION_MODE, SimulationViewer, Unit } from 'archilyse-ui-components';
import { Switch } from '@material-ui/core/';

import { useRouter } from 'Common/hooks';
import { inView } from 'Components/DataView/modules';
import { C } from 'Common';
import { useStore } from 'Components/DataView/hooks';
import './viewDrawer.scss';

const { FLOORS, UNITS } = C.DMS_VIEWS;

const getSelectedUnits = ({ pathname }, hoveredItem, siteUnits) => {
  if (inView([FLOORS], pathname) && siteUnits?.length > 0) {
    return siteUnits.filter(unit => unit.floor_id === hoveredItem.id).map(unit => unit.client_id);
  } else if (inView([UNITS], pathname)) {
    return [hoveredItem.name];
  }
  return [];
};

const ThreeDView = ({ buildingId, showToggles }) => {
  const hoveredItem = useStore(state => state.hoveredItem);
  const currentUnits: Unit[] = useStore(state => state.currentUnits);

  const [withContext, setWithContext] = useState(true);
  const [colorizeByPrice, setColorizeByPrice] = useState(false);

  const showPriceDimensionToggle = currentUnits.some((unit: Unit) => unit.ph_final_gross_rent_annual_m2);
  const routerData = useRouter();
  const selectedUnits = hoveredItem ? getSelectedUnits(routerData, hoveredItem, currentUnits) : [];
  if (!buildingId) {
    return <LoadingIndicator />;
  }
  return (
    <>
      <SimulationViewer
        buildingId={Number(buildingId)}
        simType={withContext ? SIMULATION_MODE.THREE_D_VECTOR : SIMULATION_MODE.DASHBOARD}
        highlighted3dUnits={selectedUnits}
        currentUnits={currentUnits}
        colorizeByPrice={colorizeByPrice}
        context3dUnits={(currentUnits || []).map(unit => String(unit.client_id || unit.floor_number))}
      />
      {showToggles && (
        <div className="toggles">
          {showPriceDimensionToggle && (
            <div className="map-switch-container">
              <label>
                <Switch
                  checked={colorizeByPrice}
                  size={'small'}
                  className="option-switch"
                  onChange={() => setColorizeByPrice(!colorizeByPrice)}
                  name="showBlocked"
                />
                <span id="switch-title">Price dimension</span>
              </label>
            </div>
          )}
          <div className="map-switch-container">
            <label>
              <Switch
                checked={withContext}
                size={'small'}
                className="option-switch"
                onChange={() => setWithContext(!withContext)}
                name="showBlocked"
              />
              <span id="switch-title">Map</span>
            </label>
          </div>
        </div>
      )}
    </>
  );
};

export default ThreeDView;
