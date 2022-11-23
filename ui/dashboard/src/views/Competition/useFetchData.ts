import { RequestStateType, RequestStatus, SnackbarContext } from 'archilyse-ui-components';
import { useContext, useEffect, useReducer } from 'react';
import { C } from '../../common';
import {
  CompetitionMainCategoryResponseType,
  CompetitionScoresResponseType,
  CompetitionType,
  CompetitionWeightsResponseType,
  CompetitorResponseType,
  CompetitorsUnitsResponse,
} from '../../common/types';
import { ProviderRequest } from '../../providers';

export type CompetitionState = {
  categories: RequestStateType<CompetitionMainCategoryResponseType[]>;
  competition: RequestStateType<CompetitionType>;
  competitors: RequestStateType<CompetitorResponseType[]>;
  competitorsUnits: RequestStateType<CompetitorsUnitsResponse[]>;
  scores: RequestStateType<CompetitionScoresResponseType[]>;
};

type CategoriesActions =
  | { type: 'categories/pending' }
  | { type: 'categories/fulfilled'; payload: CompetitionMainCategoryResponseType[] }
  | { type: 'categories/rejected'; error: string };

type CompetitionActions =
  | { type: 'competition/pending' }
  | { type: 'competition/fulfilled'; payload: CompetitionType }
  | { type: 'competition/rejected'; error: string }
  | { type: 'weights/update'; payload: CompetitionWeightsResponseType };

type CompetitorsActions =
  | { type: 'competitors/pending' }
  | { type: 'competitors/fulfilled'; payload: CompetitorResponseType[] }
  | { type: 'competitors/rejected'; error: string };

type CompetitorsUnitsActions =
  | { type: 'competitorsUnits/pending' }
  | { type: 'competitorsUnits/fulfilled'; payload: CompetitorsUnitsResponse[] }
  | { type: 'competitorsUnits/rejected'; error: string };

type ScoresActions =
  | { type: 'scores/pending' }
  | { type: 'scores/fulfilled'; payload: CompetitionScoresResponseType[] }
  | { type: 'scores/rejected'; error: string };

type Actions = CategoriesActions | CompetitionActions | CompetitorsActions | ScoresActions | CompetitorsUnitsActions;

type Reducer = (state: CompetitionState, action: Actions) => CompetitionState;

const initialState: CompetitionState = {
  categories: {
    data: [],
    status: RequestStatus.IDLE,
    error: null,
  },
  competition: {
    data: null,
    status: RequestStatus.IDLE,
    error: null,
  },
  competitors: {
    data: [],
    status: RequestStatus.IDLE,
    error: null,
  },
  competitorsUnits: {
    data: [],
    status: RequestStatus.IDLE,
    error: null,
  },
  scores: {
    data: [],
    status: RequestStatus.IDLE,
    error: null,
  },
};

const reducer: Reducer = (state, action) => {
  switch (action.type) {
    case 'categories/pending':
      return { ...state, categories: { ...state.categories, status: RequestStatus.PENDING } };
    case 'categories/fulfilled':
      return { ...state, categories: { status: RequestStatus.FULFILLED, data: action.payload, error: null } };
    case 'categories/rejected':
      return { ...state, categories: { status: RequestStatus.REJECTED, data: [], error: action.error } };

    case 'competition/pending':
      return { ...state, weights: { ...state.competition, status: RequestStatus.PENDING } };
    case 'competition/fulfilled':
      return { ...state, competition: { status: RequestStatus.FULFILLED, data: action.payload, error: null } };
    case 'competition/rejected':
      return { ...state, competition: { ...state.competition, status: RequestStatus.REJECTED, error: action.error } };

    case 'weights/update':
      return {
        ...state,
        competition: {
          status: RequestStatus.FULFILLED,
          data: { ...state.competition.data, weights: action.payload },
          error: null,
        },
      };

    case 'competitors/pending':
      return { ...state, competitors: { ...state.competitors, status: RequestStatus.PENDING } };
    case 'competitors/fulfilled':
      return { ...state, competitors: { status: RequestStatus.FULFILLED, data: action.payload, error: null } };
    case 'competitors/rejected':
      return { ...state, competitors: { status: RequestStatus.REJECTED, data: [], error: action.error } };

    case 'competitorsUnits/pending':
      return { ...state, competitorsUnits: { ...state.competitorsUnits, status: RequestStatus.PENDING } };
    case 'competitorsUnits/fulfilled':
      return { ...state, competitorsUnits: { status: RequestStatus.FULFILLED, data: action.payload, error: null } };
    case 'competitorsUnits/rejected':
      return { ...state, competitorsUnits: { status: RequestStatus.REJECTED, data: [], error: action.error } };

    case 'scores/pending':
      return { ...state, scores: { ...state.scores, status: RequestStatus.PENDING } };
    case 'scores/fulfilled':
      return { ...state, scores: { status: RequestStatus.FULFILLED, data: action.payload, error: null } };
    case 'scores/rejected':
      return { ...state, scores: { status: RequestStatus.REJECTED, data: [], error: action.error } };

    default:
      return state;
  }
};

const useFetchData = (competitionId: string) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const snackbar = useContext(SnackbarContext);

  const saveWeights = async weights => {
    dispatch({ type: 'competition/pending' });
    try {
      const result = await ProviderRequest.put(C.ENDPOINTS.COMPETITION_WEIGHTS(competitionId), weights);

      snackbar.show({ message: 'Weights successfully changed', severity: 'success' });
      dispatch({ type: 'weights/update', payload: result });

      loadScores();
    } catch (error) {
      dispatch({ type: 'competition/rejected', error: 'Error updating the weights' });
    }
  };

  const loadCategories = async () => {
    dispatch({ type: 'categories/pending' });
    try {
      const result = await ProviderRequest.get(C.ENDPOINTS.COMPETITION_CATEGORIES(competitionId));
      dispatch({ type: 'categories/fulfilled', payload: result });
    } catch (error) {
      dispatch({ type: 'categories/rejected', error: 'Error while loading categories' });
    }
  };
  const loadWeights = async () => {
    dispatch({ type: 'competition/pending' });
    try {
      const result = await ProviderRequest.get(C.ENDPOINTS.COMPETITION_INFO(competitionId));
      dispatch({ type: 'competition/fulfilled', payload: result });
    } catch (error) {
      dispatch({ type: 'competition/rejected', error: 'Error while loading weights' });
    }
  };
  const loadCompetitors = async () => {
    dispatch({ type: 'competitors/pending' });
    try {
      const result = await ProviderRequest.get(C.ENDPOINTS.COMPETITION_COMPETITORS(competitionId));
      dispatch({ type: 'competitors/fulfilled', payload: result });
    } catch (error) {
      dispatch({ type: 'competitors/rejected', error: 'Error while loading competitors' });
    }
  };
  const loadScores = async () => {
    dispatch({ type: 'scores/pending' });
    try {
      const result = await ProviderRequest.get(C.ENDPOINTS.COMPETITION_SCORES(competitionId));
      dispatch({ type: 'scores/fulfilled', payload: result });
    } catch (error) {
      dispatch({ type: 'scores/rejected', error: 'Error while loading scores' });
    }
  };
  const loadCompetitorUnits = async () => {
    dispatch({ type: 'competitorsUnits/pending' });
    try {
      const result = await ProviderRequest.get(C.ENDPOINTS.COMPETITION_COMPETITORS_UNITS(competitionId));
      dispatch({ type: 'competitorsUnits/fulfilled', payload: result });
    } catch (error) {
      dispatch({ type: 'competitorsUnits/rejected', error: 'Error while loading units of competitors' });
    }
  };

  useEffect(() => {
    loadCategories();
    loadWeights();
    loadCompetitors();
    loadScores();
    loadCompetitorUnits();
  }, []);

  const actions = {
    saveWeights,
    updateCompetitors: loadCompetitors,
    updateScores: loadScores,
  };

  return { state, actions };
};

export default useFetchData;
