import React from 'react';
import useSWR from 'swr';
import { C } from 'Common';
import { EntityView } from 'Components';
import formFields from 'Common/forms/building';
import { ProviderRequest } from 'Providers';

// @TODO: Review title
const NewBuilding = ({ siteId, onAdd }) => {
  const { data: site = {} } = useSWR(C.ENDPOINTS.SITE_BY_ID(siteId), ProviderRequest.get);
  return (
    <EntityView
      fields={formFields}
      entity={{}}
      parent={site}
      parentKey={'site_id'}
      context="building"
      onSubmit={onAdd}
    />
  );
};

export default NewBuilding;
