/*eslint prefer-rest-params: warn */
/*eslint @typescript-eslint/no-this-alias: warn */

export default (func: Function, delay: number) => {
  let timer: any;

  return function (...args) {
    clearTimeout(timer);

    timer = setTimeout(() => {
      func.apply(this, args);
    }, delay);
  };
};
