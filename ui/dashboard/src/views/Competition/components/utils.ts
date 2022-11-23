export const getSafePercents = (percents: number): [string, number] => {
  if (typeof percents !== 'number') return ['—', 0];

  const roundedPercents = Math.round(percents * 1000) / 10; // 0.xxx to xx.x
  if (roundedPercents > 100) {
    return ['100%', 100];
  }
  if (roundedPercents < 0) {
    return ['0%', 0];
  }

  return [`${roundedPercents}%`, roundedPercents];
};

export function checkIsExpanded(categoryKey: string, expandedCategories: string[]): boolean {
  return expandedCategories.some(item => {
    // key and path is a string like 'xxx.yyy.zzz'
    const categoryPath = categoryKey.split('.');
    const expandedPath = item.split('.');

    return categoryPath.every((_, index) => categoryPath[index] === expandedPath[index]);
  });
}
