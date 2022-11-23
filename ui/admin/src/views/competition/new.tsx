import React from 'react';
import useSWR from 'swr';
import { useRouter } from '../../common/hooks';
import { EntityView } from '../../components';
import formFields from '../../common/forms/competition';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';

const Competition = () => {
  const { query } = useRouter();
  const { data: client = {} } = useSWR(C.ENDPOINTS.CLIENT(query.client_id), ProviderRequest.get);
  const { data: sites = [] } = useSWR(C.ENDPOINTS.SITE_NAMES(query.client_id), ProviderRequest.get);
  formFields.map(field => {
    if (field.name === 'competitors') {
      field.options = sites.map(site => ({ label: site.name, value: site.id }));
    }
    return field;
  });
  return <EntityView fields={formFields} entity={{}} parent={client} parentKey={'client_id'} context="competition" />;
};

export default Competition;
