import React from 'react';
import useSWR from 'swr';
import { useRouter } from '../../common/hooks';
import { ProviderRequest } from '../../providers';
import EntityView from '../../components/EntityView';
import formFields from '../../common/forms/competition';
import { C } from '../../common';

const Competition = () => {
  const { params } = useRouter();
  const { data: competition } = useSWR(C.ENDPOINTS.COMPETITION_ADMIN(params.id), ProviderRequest.get);
  const client_id = competition !== undefined ? competition.client_id : null;
  const { data: sites = [] } = useSWR(C.ENDPOINTS.SITE_NAMES(client_id), ProviderRequest.get);

  if (!competition) return null;
  formFields.map(field => {
    if (field.name === 'competitors') {
      field.options = sites.map(site => ({ label: site.name, value: site.id }));
    }
    return field;
  });

  competition.red_flags_enabled = String(competition.red_flags_enabled);
  competition.prices_are_rent = String(competition.prices_are_rent);

  return <EntityView fields={formFields} entity={competition} context="competition" />;
};

export default Competition;
