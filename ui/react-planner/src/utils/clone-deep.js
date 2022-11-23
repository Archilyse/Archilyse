const cloneDeep = obj => {
  // @TODO: To common module once we handle es6 imports in Jest
  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }

  if (obj instanceof Array) {
    return obj.reduce((arr, item, i) => {
      arr[i] = cloneDeep(item);
      return arr;
    }, []);
  }

  if (obj instanceof Object) {
    return Object.keys(obj).reduce((cloneObj, key) => {
      cloneObj[key] = cloneDeep(obj[key]);
      return cloneObj;
    }, {});
  }
};

export default cloneDeep;
