import React from 'react';
import useSWR from 'swr';
import { useRouter } from '../../common/hooks';
import { SiteView } from '../../components';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';

const Site = () => {
  const { query } = useRouter();
  const { data: client = {} } = useSWR(C.ENDPOINTS.CLIENT(query.client_id), ProviderRequest.get);

  return <SiteView parent={client} site={{ simulation_version: 'PH_2022_H1' }} />;
};

export default Site;
