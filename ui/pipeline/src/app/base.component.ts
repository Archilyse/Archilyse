import { parseErrorObj } from './_shared-libraries/Url';
import { environment } from '../environments/environment';
import { getUserInfo } from './_services/auth.interceptor';
export const SAVING = 'Saving...';
export const SAVED = 'Saved';
export const SAVE = 'Save';

/**
 * Common elements for base components.
 */
export class BaseComponent {
  error = null;
  loading = false;

  plan_id: string;
  site_id: string;
  client_site_id: string;
  scale: number;
  planData;

  saving = false;
  saveText = SAVED;
  savingText = null;
  saveDisabled = true;

  loadMetrics(planId: number) {
    if (window.sa_pageview) {
      const user = getUserInfo();
      window.sa_pageview(window.location.pathname, { group_id: user?.group_id, plan_id: planId });
    }
  }

  loadOnNewParameters(activatedRoute, onLoad, loadParams, optional = false) {
    if (activatedRoute?.params) {
      return activatedRoute.params.subscribe(() => {
        const params = activatedRoute.snapshot.params;
        let reload = false;
        loadParams.forEach(param => {
          if (this[param] !== params[param]) {
            this[param] = params[param];
            reload = true;
          }
        });

        // Reload only if a parameter changed
        if (reload || optional) {
          onLoad();
        }
      });
    }
  }

  parseError(e) {
    if (environment.displayErrors) {
      console.error('DEBUG', e);
    }
    this.error = parseErrorObj(e);
    this.loading = false;
  }

  /**
   * If the content changed, we allow the user to store
   */
  contentChanged() {
    this.saveText = SAVE;
    this.saveDisabled = false;
  }

  /**
   * The content was reloaded
   */
  contentNew() {
    this.error = null;
    this.loading = false;
    this.saving = false;
    this.saveText = SAVED;
    this.saveDisabled = true;
  }

  /**
   * We request the api the plan data
   * We also get georef_scale or we set a default when not set.
   * @param apiService
   * @param plan_id
   */
  async requestPlanData(apiService, plan_id) {
    if (plan_id) {
      this.loadMetrics(Number(plan_id));
      // We require to set it to null so the content reload.
      this.planData = null;
      this.planData = await apiService.getPlanData(plan_id);
      this.plan_id = plan_id;
      this.site_id = this.planData.site_id;
      this.scale = this.planData['georef_scale'];
    } else {
      console.error('Plan id is null');
    }
  }
}
