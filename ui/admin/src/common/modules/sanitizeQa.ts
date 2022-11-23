export default (qa, defaultQaHeaders) => {
  if (!qa || !qa.data) return {};
  const sanitizedQa = Object.keys(qa.data).reduce((newQaData, clientId) => {
    const newQaRow = Object.keys(qa.data[clientId])
      .filter(name => defaultQaHeaders?.includes(name))
      .reduce((qaRow, qaValue) => {
        qaRow[qaValue] = qa.data[clientId][qaValue];
        return qaRow;
      }, {});
    newQaData[clientId] = newQaRow;
    return newQaData;
  }, {});
  return sanitizedQa;
};
