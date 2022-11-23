export default data => {
  Object.keys(data).forEach(key => {
    if (!data[key]) delete data[key];
  });
};
