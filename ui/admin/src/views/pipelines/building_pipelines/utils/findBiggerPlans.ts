import { C } from 'Common';
import { ProviderRequest } from 'Providers';

// @TODO: All of this to an util file
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

const findBiggerPlans = async (pipelines, masterPlan: { id: number; building_id: number }): Promise<string[]> => {
  const planSizes = await fetchPlanSizes(pipelines, masterPlan);
  const currentSize = planSizes.find(plan => String(plan.id) === String(masterPlan.id));

  const biggerPlans = planSizes.filter(
    plan => currentSize.image_width < plan.image_width || currentSize.image_height < plan.image_height
  );

  return biggerPlans.map(p => p.id);
};

export default findBiggerPlans;
