import { useRef } from 'react';

export default (func: () => void): void => {
  const mounted = useRef(false);

  if (!mounted.current) func();

  mounted.current = true;
};
