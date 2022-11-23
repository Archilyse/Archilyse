import { useParams } from 'react-router-dom';

export const usePlanId = (): number => {
  const params: any = useParams();
  return Number(params.id);
};
