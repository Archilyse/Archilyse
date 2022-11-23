import { RequestStateType, RequestStatus } from 'archilyse-ui-components';
import { useReducer } from 'react';
import { C } from '../../../../common';
import { CompetitorClientInput } from '../../../../common/types';
import { ProviderRequest } from '../../../../providers';

type Actions =
  | { type: RequestStatus.PENDING }
  | { type: RequestStatus.FULFILLED; payload?: CompetitorClientInput[] }
  | { type: RequestStatus.REJECTED; error: string };

const initialUploadState: RequestStateType = {
  data: null,
  status: RequestStatus.IDLE,
  error: null,
};

const initialLoadState: RequestStateType<CompetitorClientInput[]> = {
  data: [],
  status: RequestStatus.IDLE,
  error: null,
};

const reducer = (state: RequestStateType, action: Actions) => {
  switch (action.type) {
    case RequestStatus.PENDING:
      return { ...state, status: RequestStatus.PENDING };
    case RequestStatus.FULFILLED:
      return { ...state, status: RequestStatus.FULFILLED, data: action.payload };
    case RequestStatus.REJECTED:
      return { ...state, status: RequestStatus.REJECTED, error: action.error };

    default:
      return state;
  }
};

const useCompetitorsData = (competitionId: string) => {
  const [uploadState, uploadDispatch] = useReducer(reducer, initialUploadState);
  const [loadState, loadDispatch] = useReducer(reducer, initialLoadState);

  const load = async competitors => {
    loadDispatch({ type: RequestStatus.PENDING });
    try {
      const requests = competitors.map(({ id }) =>
        ProviderRequest.get(C.ENDPOINTS.COMPETITION_COMPETITOR_CLIENT_INPUT(competitionId, id))
      );
      const result: CompetitorClientInput[] = await Promise.all(requests);

      loadDispatch({ type: RequestStatus.FULFILLED, payload: result });
    } catch (error) {
      loadDispatch({ type: RequestStatus.REJECTED, error: 'Error while loading data' });
    }
  };

  const save = async fields => {
    uploadDispatch({ type: RequestStatus.PENDING });
    try {
      const requests = Object.keys(fields).map(competitorId =>
        ProviderRequest.put(
          C.ENDPOINTS.COMPETITION_COMPETITOR_CLIENT_INPUT(competitionId, competitorId),
          fields[competitorId]
        )
      );
      await Promise.all(requests);

      uploadDispatch({ type: RequestStatus.FULFILLED });
    } catch (error) {
      uploadDispatch({ type: RequestStatus.REJECTED, error: 'Error while saving raw data' });
    }
  };

  const state = {
    loaded: loadState,
    uploaded: uploadState,
  };

  const actions = {
    load,
    save,
  };

  return { state, actions };
};

export default useCompetitorsData;
