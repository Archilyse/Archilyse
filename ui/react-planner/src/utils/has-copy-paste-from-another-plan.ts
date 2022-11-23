import { ProviderStorage } from 'archilyse-ui-components';
import { STORAGE } from '../constants';
import { StorageCopyPaste } from '../types';

export default planId => {
  if (!planId) return false;
  const copy: StorageCopyPaste = JSON.parse(ProviderStorage.get(STORAGE.COPY_PASTE) || null);
  const hasCopyFromAnotherPlan = copy && Number(copy.planId) !== Number(planId);
  return hasCopyFromAnotherPlan;
};
