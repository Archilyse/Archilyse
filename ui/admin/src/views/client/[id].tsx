import React from 'react';
import useSWR from 'swr';
import { useRouter } from '../../common/hooks';
import { ProviderRequest } from '../../providers';
import EntityView from '../../components/EntityView';
import formFields from '../../common/forms/client';
import { C } from '../../common';

const Client = () => {
  const { params } = useRouter();
  const { data: client } = useSWR(C.ENDPOINTS.CLIENT(params.id), ProviderRequest.get);
  if (!client) return null;
  return <EntityView fields={formFields} entity={client} context="client" />;
};

export default Client;
