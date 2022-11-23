export function objectsMap(object, func) {
  const mappedObject = {};
  for (const key in object) {
    mappedObject[key] = func(key, mappedObject[key]);
  }
  return mappedObject;
}

export function objectsCompare(x, y) {
  if (x === y) return true;
  if (!(x instanceof Object) || !(y instanceof Object)) return false;
  if (x.constructor !== y.constructor) return false;

  for (const p in x) {
    if (!x.hasOwnProperty(p)) continue;
    if (!y.hasOwnProperty(p)) return false;
    if (x[p] === y[p]) continue;
    if (typeof x[p] !== 'object') return false;
    if (!objectsCompare(x[p], y[p])) return false;
  }

  for (const p in y) {
    if (y.hasOwnProperty(p) && !x.hasOwnProperty(p)) return false;
  }

  return true;
}
