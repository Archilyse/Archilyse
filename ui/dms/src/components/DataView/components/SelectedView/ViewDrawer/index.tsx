import React from 'react';
import { Widget } from 'archilyse-ui-components';
import { useRouter } from 'Common/hooks';
import { inView } from 'Components/DataView/modules';
import { C } from 'Common';
import { WIDGETS_TABS } from '../widgets';
import MarkersMap from './MarkersMap';
import ThreeDView from './ThreeDView';
import './viewDrawer.scss';

const { SITES, BUILDINGS, FLOORS, UNITS, ROOMS } = C.DMS_VIEWS;

const insideBuilding = pathname => inView([FLOORS, UNITS, ROOMS], pathname);

const getTabs = (pathname): [string[], number] => {
  const tabs = [];
  const showMap = inView([SITES, BUILDINGS], pathname);
  const show3d = insideBuilding(pathname);
  const showUnitFloorplan = inView([ROOMS], pathname);
  if (showMap) {
    tabs.push(WIDGETS_TABS.MAP);
  }

  if (show3d) {
    tabs.push(WIDGETS_TABS.THREE_D);
  }

  if (showUnitFloorplan) {
    tabs.push(WIDGETS_TABS.FLOORPLAN);
  }
  const initialTab = 0; // Always the first tab (either the map or the 3d)
  return [tabs, initialTab];
};

const ViewDrawer = ({ buildingId, unitFloorPlan }) => {
  const { pathname } = useRouter();
  const [tabs, initialTab] = getTabs(pathname);
  if (!tabs.length) return null;
  return (
    <Widget className={'view-drawer'} initialTab={initialTab} tabHeaders={tabs}>
      {tabs.includes(WIDGETS_TABS.MAP) && (
        <div className="map-container">
          <MarkersMap pathname={pathname} />
        </div>
      )}
      {tabs.includes(WIDGETS_TABS.THREE_D) && (
        <div className="view-drawer-simulation-container">
          <ThreeDView buildingId={buildingId} showToggles={tabs.length === 1} />
        </div>
      )}
      {tabs.includes(WIDGETS_TABS.FLOORPLAN) && (
        <div className="unit-floorplan">
          <a href={unitFloorPlan} rel="noreferrer" target="_blank">
            <img id="floorplan-image" className="floorplan-image" src={unitFloorPlan} />
          </a>
        </div>
      )}
    </Widget>
  );
};

export default ViewDrawer;
