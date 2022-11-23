export default number => {
  if (number !== 0 && !number) {
    return;
  }

  const result = Math.round(number * 10000) / 100;

  return result + '%';
};
