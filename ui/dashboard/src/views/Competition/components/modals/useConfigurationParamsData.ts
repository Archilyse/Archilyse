import { RequestStateType, RequestStatus } from 'archilyse-ui-components';
import { useEffect, useState } from 'react';
import { C } from '../../../../common';
import {
  CompetitionConfigurationParamsResponseType,
  FlatDeviationResponseType,
  ShowersBathtubsDistributionResponseType,
} from '../../../../common/types';
import { ProviderRequest } from '../../../../providers';

type Props = {
  field: keyof CompetitionConfigurationParamsResponseType;
};
const withoutNullable = (data: (ShowersBathtubsDistributionResponseType | FlatDeviationResponseType)[]) => {
  Object.keys(data).forEach(key => {
    if (data[key] === null) data[key] = 0;
  });

  return data;
};

const initialParams: RequestStateType<CompetitionConfigurationParamsResponseType> = {
  data: {
    flat_types_distribution: [],
    showers_bathtubs_distribution: [],
  },
  status: RequestStatus.IDLE,
  error: null,
};

const initialUpdated: RequestStateType = {
  data: null,
  status: RequestStatus.IDLE,
  error: null,
};

function useConfigurationParamsData({ field }: Props) {
  const [params, setParams] = useState(initialParams);
  const [updated, setUpdated] = useState(initialUpdated);

  const loadData = async () => {
    setParams({ ...params, status: RequestStatus.PENDING });

    try {
      const data = await ProviderRequest.get<CompetitionConfigurationParamsResponseType>(
        C.ENDPOINTS.COMPETITION_PARAMETERS(1)
      );

      setParams({ ...params, data, status: RequestStatus.FULFILLED });
    } catch (error) {
      console.log(error);
      setParams({ ...params, status: RequestStatus.REJECTED });
    }
  };

  const saveData = async () => {
    setUpdated({ ...updated, status: RequestStatus.PENDING });
    try {
      const processedData = { [field]: withoutNullable(params.data[field]) };

      const updatedData = await ProviderRequest.put<CompetitionConfigurationParamsResponseType>(
        C.ENDPOINTS.COMPETITION_PARAMETERS(1),
        processedData
      );

      setParams({ ...params, data: updatedData });
      setUpdated({ ...updated, status: RequestStatus.FULFILLED });
    } catch (error) {
      console.log(error);
      setUpdated({ ...updated, status: RequestStatus.REJECTED });
    }
  };

  const handleUpdateData = (newData: FlatDeviationResponseType[] | ShowersBathtubsDistributionResponseType[]) => {
    setParams({ ...params, data: { ...params.data, [field]: newData } });
  };

  useEffect(() => {
    loadData();
  }, []);

  return { params, updated, updateData: handleUpdateData, saveData };
}

export default useConfigurationParamsData;
