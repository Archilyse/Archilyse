import React from 'react';

const WithSuffix = ({ children: num }: React.PropsWithChildren<{}>): JSX.Element => {
  if (typeof num !== 'number') {
    return null;
  }

  let suffix = 'th';
  if (String(num).endsWith('1') && num !== 11) {
    suffix = 'st';
  }
  if (String(num).endsWith('2') && num !== 12) {
    suffix = 'nd';
  }
  if (String(num).endsWith('3') && num !== 13) {
    suffix = 'rd';
  }

  return (
    <>
      <span className="position">{num}</span>
      {suffix}
    </>
  );
};

export default WithSuffix;
