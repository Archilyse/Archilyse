import React from 'react';
import C from '../../../../common/src/constants';
import { SiteStructure } from '../../types';
import Panel from './panel';

type PanelSiteStructureProps = {
  siteStructure: SiteStructure;
};

const UL_STYLE = { listStyleType: 'none', paddingRight: '20px', paddingLeft: '20px' };
const LI_STYLE = { display: 'flex', justifyContent: 'space-between', marginBottom: '5px' };
const A_STYLE = { textDecoration: 'none', color: C.COLORS.PRIMARY };

const parseSiteStructure = (siteStructure: SiteStructure) => {
  const { site, building, floors, planId } = siteStructure;

  return {
    client_site_id: siteStructure.client_site_id,
    site_id: site.id,
    site: `${site.name} - (${site.id})`,
    building: `${building.street}, ${building.housenumber} - (${building.id})`,
    floors: `${floors
      .filter(floor => Number(floor.plan_id) === Number(planId))
      .map(f => f.floor_number)
      .join(', ')} - (${planId})`,
  };
};

const PanelSiteStructureProps = ({ siteStructure }: PanelSiteStructureProps) => {
  const parsedStructure = parseSiteStructure(siteStructure);
  const adminURL = '/admin';

  return (
    <Panel name={'Site structure'} opened={true}>
      <ul style={UL_STYLE}>
        <li style={LI_STYLE}>
          <div>Client site ID:</div>
          <div>{parsedStructure.client_site_id}</div>
        </li>
        <li style={LI_STYLE}>
          <div>Site:</div>
          <div>
            <a style={A_STYLE} href={`${adminURL}/pipelines?site_id=${parsedStructure.site_id}`} target="blank">
              {parsedStructure.site}
            </a>
          </div>
        </li>
        <li style={LI_STYLE}>
          <div>Building:</div>
          <div>{parsedStructure.building}</div>
        </li>
        <li style={LI_STYLE}>
          <div>Floors: </div>
          <div>
            <a style={A_STYLE} href={`${adminURL}/pipelines?site_id=${parsedStructure.site_id}`} target="blank">
              {parsedStructure.floors}
            </a>
          </div>
        </li>
      </ul>
    </Panel>
  );
};

export default PanelSiteStructureProps;
