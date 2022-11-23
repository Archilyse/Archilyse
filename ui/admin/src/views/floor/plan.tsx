import React from 'react';
import { useRouter } from '../../common/hooks';
import { getUrlForRequests } from '../../providers/request';
import { C } from '../../common';
import './plan.scss';

const Plan = () => {
  const { query } = useRouter();
  const { plan_id } = query;

  if (!plan_id) return null;

  return <img id={'original-plan'} src={`${getUrlForRequests()}/${C.ENDPOINTS.RAW_PLAN_IMAGE(plan_id)}`}></img>;
};

export default Plan;
