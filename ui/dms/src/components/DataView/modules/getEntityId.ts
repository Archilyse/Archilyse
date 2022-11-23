const getEntityId = (hierarchy = [], key) => {
  const found = hierarchy.find(item => item.href && item.href.includes(key));
  if (!found) {
    return null;
  }
  const [entityId] = found.href.split('=').slice(-1);
  return entityId;
};

export default getEntityId;
