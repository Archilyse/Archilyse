import { useEffect, useState } from 'react';
import { auth, ProviderRequest } from 'archilyse-ui-components';
import { CompetitionType } from '../../common/types';
import { C } from '../../common';
import './competitions.scss';

const useFetchData = () => {
  const [competitions, setCompetitions] = useState<CompetitionType[]>([]);
  const [clientName, setClientName] = useState('');

  const loadClientName = async () => {
    const userInfo = auth.getUserInfo();
    const client = await ProviderRequest.get(C.ENDPOINTS.CLIENT(userInfo.client_id));
    setClientName(client?.name);
  };

  const loadCompetitions = async () => {
    const competitions: CompetitionType[] = await ProviderRequest.get(C.ENDPOINTS.COMPETITIONS());
    setCompetitions(competitions);
  };

  useEffect(() => {
    loadClientName();
    loadCompetitions();
  }, []);
  return { competitions, clientName };
};

export default useFetchData;
