export default (word: string): string => {
  if (!word) return '';
  return word.charAt(0).toUpperCase() + word.substring(1);
};
