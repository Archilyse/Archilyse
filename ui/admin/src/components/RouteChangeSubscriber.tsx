import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import * as savedRoute from '../common/modules/savedRoute';

export default () => {
  const location = useLocation();

  useEffect(savedRoute.update, [location]);

  return null;
};
