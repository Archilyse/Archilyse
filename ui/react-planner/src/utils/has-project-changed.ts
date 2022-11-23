import getProjectHashCode from './get-project-hash-code';

export default state => {
  const initialProjectHash = state.projectHashCode;
  const currentProjectHash = getProjectHashCode(state);
  return initialProjectHash !== currentProjectHash;
};
