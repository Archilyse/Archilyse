import { useEffect, useState } from 'react';

export default () => {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handlePlannerMouseMove = event =>
    setPosition({ x: parseFloat(event.position.x), y: parseFloat(event.position.y) });

  useEffect(() => {
    document.addEventListener('mousemove-planner-event', handlePlannerMouseMove);

    return () => {
      document.removeEventListener('mousemove-planner-event', handlePlannerMouseMove);
    };
  });

  return position;
};
