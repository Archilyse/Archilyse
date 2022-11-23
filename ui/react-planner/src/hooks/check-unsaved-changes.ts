import { useEffect } from 'react';

export default projectHasChanges => {
  useEffect(() => {
    const checkSavedChanges = event => {
      if (projectHasChanges) {
        event.preventDefault(); // To show alert in firefox
        event.returnValue = 'Exiting without saving changes'; // To show it in Chrome returnValue must be truthy
      }
    };
    window.addEventListener('beforeunload', checkSavedChanges);
    return () => {
      window.removeEventListener('beforeunload', checkSavedChanges);
    };
  }, [projectHasChanges]);
};
