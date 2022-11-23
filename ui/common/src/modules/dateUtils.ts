class DateUtils {
  static getTimeFromISOString = (isoDate: string): string => {
    if (!isoDate) return '-';

    const date = DateUtils._getDate(isoDate);

    return date.toLocaleTimeString();
  };

  static getDateFromISOString = (isoDate: string): string => {
    if (!isoDate) return '-';

    const date = DateUtils._getDate(isoDate);

    return date.toLocaleDateString();
  };

  static getFullDateFromISOString = (isoDate: string): string => {
    if (!isoDate) return '-';

    const date = DateUtils._getDate(isoDate);

    return date.toLocaleString();
  };

  static _getDate = (isoDate: string): Date => {
    let utcISOString = isoDate;
    if (!utcISOString.includes('Z')) {
      utcISOString = `${utcISOString}Z`;
    }

    return new Date(utcISOString);
  };
}

export default DateUtils;
