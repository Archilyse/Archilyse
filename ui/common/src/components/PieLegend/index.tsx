import React from 'react';
import { capitalize } from '../../modules';
import './PieLegend.scss';

const formatLegend = status => capitalize(status.toLowerCase());

export default ({ data, format = true, className = '', itemStyle = (item: string) => ({}) }) => {
  return (
    <div className={`pie-legend ${className}`}>
      <ul>
        {data.map(item => {
          return (
            <li key={item}>
              <p>{format ? formatLegend(item) : item}</p>
              <div className="bar" style={itemStyle(item)}></div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
