type ValidationError = {
  is_blocking: 0 | 1;
  object_id: string;
  position: {
    coordinates: [number, number];
    type: 'Point';
  };
  text: string;
  type: string;
};

export default ValidationError;
