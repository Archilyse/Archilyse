import { hasOwnNestedProperty, isSiteSimulatedAlready, shouldSave } from './Validations';

describe('Testing Validations.ts library', () => {
  let getSiteResult;
  const apiServiceMock: any = {
    getSite: async () => getSiteResult,
    getPlanData: async () => 'site1',
  };

  it('should safely check if an object has a property', () => {
    const exampleObj = {
      innerObject: {
        deepObject: {
          value: 'Defined prop',
        },
      },
    };

    expect(hasOwnNestedProperty(exampleObj, 'innerObject.deepObject.value')).toBeTrue();
    expect(hasOwnNestedProperty(exampleObj, 'innerObject.wrongPath')).toBeFalse();
    expect(hasOwnNestedProperty(exampleObj, 'wrongPath.')).toBeFalse();
    expect(hasOwnNestedProperty(exampleObj, '.deepObject.value')).toBeFalse();
    expect(hasOwnNestedProperty(null, '.deepObject.value')).toBeFalse();
  });
  describe('isSiteSimulatedAlready', () => {
    beforeEach(() => {
      getSiteResult = { full_slam_results: 'SUCCESS', heatmaps_qa_complete: true };
    });

    it('returns false if "full_slam_results" is not "SUCCESS"', async () => {
      getSiteResult.full_slam_results = '';
      const result = await isSiteSimulatedAlready(apiServiceMock, 'plan1');
      expect(result).toBeFalse();
    });
    it('returns false if "heatmaps_qa_complete" is not "true"', async () => {
      getSiteResult.heatmaps_qa_complete = false;
      const result = await isSiteSimulatedAlready(apiServiceMock, 'plan1');
      expect(result).toBeFalse();
    });
    it('returns true if "heatmaps_qa_complete" is "true" and "full_slam_results" is "SUCCESS"', async () => {
      const result = await isSiteSimulatedAlready(apiServiceMock, 'plan1');
      expect(result).toBeTrue();
    });
  });
  describe('shouldSave', () => {
    let confirmResult;
    beforeEach(() => {
      getSiteResult = { full_slam_results: 'SUCCESS', heatmaps_qa_complete: true };
      spyOn(window, 'confirm').and.callFake(() => confirmResult);
    });

    it('shows a confirm dialog if the site has been simulated already', async () => {
      await shouldSave(apiServiceMock, 'plan1');
      expect(window.confirm).toHaveBeenCalled();
    });
    it('shows a confirm dialog if the site has been simulated already and returns true if it is been accepted', async () => {
      confirmResult = true;
      const result = await shouldSave(apiServiceMock, 'plan1');
      expect(result).toBeTrue();
    });
    it('shows a confirm dialog if the site has been simulated already and returns false if it is been denied', async () => {
      confirmResult = false;
      const result = await shouldSave(apiServiceMock, 'plan1');
      expect(result).toBeFalse();
    });
    it('does not shows any confirm dialog if the site has not been simulated already and returns true', async () => {
      getSiteResult.heatmaps_qa_complete = false;
      const result = await shouldSave(apiServiceMock, 'plan1');
      expect(window.confirm).not.toHaveBeenCalled();
      expect(result).toBeTrue();
    });
  });
});
