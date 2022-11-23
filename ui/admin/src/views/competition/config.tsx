import React, { useContext } from 'react';
import { ProviderRequest } from 'Providers';
import { C } from 'Common';
import useSWR from 'swr';
import { useRouter } from 'Common/hooks';
import { SnackbarContext } from 'archilyse-ui-components';
import { CompetitionConfigView } from 'Components';

const CompetitionConfig = () => {
  const snackbar = useContext(SnackbarContext);
  const { params } = useRouter();
  const { data: competition } = useSWR(C.ENDPOINTS.COMPETITION_ADMIN(params.id), ProviderRequest.get);
  const { data: categories } = useSWR(C.ENDPOINTS.COMPETITION_CATEGORIES(), ProviderRequest.get);
  if (!competition || !categories) return null;

  const onSubmit = async competition => {
    await ProviderRequest.put(C.ENDPOINTS.COMPETITION_ADMIN(params.id), {
      configuration_parameters: competition.configuration_parameters,
    });
    snackbar.show({ message: 'Saved successfully', severity: 'success' });
  };
  return <CompetitionConfigView competition={competition} categories={categories} onSubmit={onSubmit} />;
};

export default CompetitionConfig;
