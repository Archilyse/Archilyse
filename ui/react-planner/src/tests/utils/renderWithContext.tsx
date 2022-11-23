import React from 'react';
import { render } from '@testing-library/react';
import AppContext from '../../AppContext';
import { MOCK_CONTEXT } from '.';

const renderWithContext = component => {
  // We need to directly "mutate/mock" the AppContext used by PanelScale
  return render(<AppContext.Provider value={MOCK_CONTEXT}>{component}</AppContext.Provider>);
};

export default renderWithContext;
