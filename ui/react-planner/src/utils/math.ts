// Returns float fixed to desired precision
export function toFixedFloat(num, precision = 6): number {
  if (num && precision) {
    return parseFloat(parseFloat(num).toFixed(precision));
  }
  return 0;
}

// Returns absolute value of a number, doesn't work for floats - only ints
export const fAbs = (n: number): number => {
  let x = n;
  x < 0 && (x = ~x + 1);
  return x;
};

export const multiplyMatrices = (m1: number[][], m2: number[][]): number[][] => {
  const result = [];
  for (let i = 0; i < m1.length; i++) {
    result[i] = [];
    for (let j = 0; j < m2[0].length; j++) {
      let sum = 0;
      for (let k = 0; k < m1[0].length; k++) {
        sum += m1[i][k] * m2[k][j];
      }
      result[i][j] = sum;
    }
  }
  return result;
};
