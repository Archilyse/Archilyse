import { ProviderRequest } from 'archilyse-ui-components';
import { batch } from 'react-redux';
import { ENDPOINTS, MODE_ROTATE_SCALE_BACKGROUND } from '../../constants';

// @TODO: Wrap all the actions below in another action/function to be used here and while loading the plan in react-planner
export async function reloadProject(planId, projectActions, currentBackground, currentScaleValidated) {
  try {
    const result = await ProviderRequest.get(ENDPOINTS.ANNOTATION_PLAN(planId, { validated: true }));
    const scene = result.data;
    scene.background = currentBackground;

    const importedProjectScaleValidated = Boolean(scene?.scale);
    const shouldSetScaleValidated = currentScaleValidated !== importedProjectScaleValidated;
    batch(() => {
      projectActions.loadProject(scene);
      projectActions.reGenerateAreas();
      projectActions.setValidationErrors(result.errors);
      projectActions.showSnackbar({
        message: 'Annotation imported succesfully',
        severity: 'success',
        duration: 2000,
      });

      projectActions.setMode(MODE_ROTATE_SCALE_BACKGROUND);
      projectActions.setMustImportAnnotations(false);
      projectActions.setProjectHashCode();
      shouldSetScaleValidated && projectActions.setScaleValidated(importedProjectScaleValidated);
    });
  } catch (error) {
    projectActions.showSnackbar({
      message: `Error when importing annotation: ${error}`,
      severity: 'error',
    });
  }
}
