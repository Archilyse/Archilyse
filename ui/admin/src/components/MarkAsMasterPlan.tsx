import { Checkbox } from '@material-ui/core';
import React from 'react';
import { C } from '../common';
import { ProviderRequest } from '../providers';

type PlanSize = {
  id: string;
  image_width: number;
  image_height: number;
};

const fetchPlanSizes = async (pipelines, masterPlan): Promise<PlanSize[]> => {
  const requests = pipelines
    .filter(pipeline => Number(pipeline.building_id) === Number(masterPlan.building_id)) // Only ones from the same building
    .map(pipelines => ProviderRequest.get(C.ENDPOINTS.PLAN(pipelines.id)));
  const plans = await Promise.all(requests);
  return plans.map((p: any) => ({ image_width: p.image_width, image_height: p.image_height, id: p.id }));
};

const findBiggerPlans = async (pipelines, masterPlan: { id: string; building_id: number }): Promise<string[]> => {
  const planSizes = await fetchPlanSizes(pipelines, masterPlan);
  const currentSize = planSizes.find(plan => String(plan.id) === String(masterPlan.id));

  const biggerPlans = planSizes.filter(
    plan => currentSize.image_width < plan.image_width || currentSize.image_height < plan.image_height
  );

  return biggerPlans.map(p => p.id);
};
export const MarkAsMasterPlanRenderer = ({ data, site, pipelines, snackbar, reloadPipelines }) => {
  const enforceMasterPlan = Boolean(site?.enforce_masterplan);

  const checked = data.is_masterplan;
  const changeCheckboxStatus = async () => {
    const planId = data.id;

    if (checked) {
      await ProviderRequest.patch(C.ENDPOINTS.PLAN(planId), { is_masterplan: false });
    } else {
      await ProviderRequest.put(C.ENDPOINTS.SET_MASTERPLAN(planId), {});
      const biggerPlans = await findBiggerPlans(pipelines, data);

      if (biggerPlans.length > 0) {
        snackbar.show({
          message: `The selected master plan is smaller than the plans: {${biggerPlans.join(
            ','
          )}}, this may affect the labelling`,
          severity: 'warning',
        });
      }
    }
    reloadPipelines();
  };

  return (
    <Checkbox
      checked={checked}
      disabled={!enforceMasterPlan}
      color="primary"
      className={`site-delivered-${checked}`}
      onChange={changeCheckboxStatus}
      name="mark_as_masterplan"
      value="primary"
      inputProps={{ 'aria-label': 'primary checkbox' }}
    />
  );
};
