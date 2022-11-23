import React from 'react';
import { capitalize, LoadingIndicator, PieChart } from 'archilyse-ui-components';
import { AreaData, DMSItem, EntityAreaRecord } from 'Common/types';
import { C } from 'Common';
import { isEntityFolder } from '../../../modules';
import './detailsDrawer.scss';

const DEFAULT_PIE_INNER_RADIUS = 70;
const HIGHLIGHTED_SLICE_INNER_RADIUS = 75;

type PieData = { x: string; y: number }[];

const MAX_INNER_LABEL_LENGTH = 14;
const SITE_ENTITIES = 'sites';
const LABEL_UNIT_AMOUNT = ' units';
const LABEL_AREA_SQUARE_METERS = 'm2';

const getChartColor = (dataSource: any, hoveredItem: DMSItem) => {
  if (Number(hoveredItem?.id) === Number(dataSource.datum.x)) {
    return C.COLORS.PRIMARY_COLOR;
  }
  const colorSet = C.COLORS.NET_AREA_DISTRIBUTION;
  const colorIndex = Math.round(dataSource.datum._x - 1) % colorSet.length;
  return colorSet[colorIndex];
};

const getMeasureUnit = (entityName: string) => {
  return entityName == SITE_ENTITIES ? LABEL_UNIT_AMOUNT : LABEL_AREA_SQUARE_METERS;
};

const getUnitWithRounding = (entityName: string, totalAmount: number) => {
  return entityName != SITE_ENTITIES ? totalAmount.toFixed(1) : totalAmount;
};

const getInnerLabel = (entityName: string, pieData: PieData, data: EntityAreaRecord[], hoveredItem: DMSItem) => {
  const measureUnit = getMeasureUnit(entityName);
  if (hoveredItem && isEntityFolder(hoveredItem)) {
    const { name } = hoveredItem;
    const itemLabel = name.length > MAX_INNER_LABEL_LENGTH ? `${name.substring(0, MAX_INNER_LABEL_LENGTH)}...` : name;
    const itemValue = pieData.find(d => d.x === String(hoveredItem.id))?.y;
    const surface = itemValue ? `${itemValue}${measureUnit}` : '';
    return `${itemLabel} \n ${surface}`;
  }
  const totalAmount = pieData.reduce((accum: number, d) => accum + d.y, 0);
  return `${getUnitWithRounding(entityName, totalAmount)}${measureUnit}`;
};

type AreaDataProps = {
  areaData: AreaData | {};
  isLoading: boolean;
  visibleItems: DMSItem[];
  hoveredItem: DMSItem;
  onHoverPieChartItem: (id: string) => {};
};

const getVisibleData = (data, visibleItems = []) => {
  const visibleSitesById = visibleItems.reduce((accum, item) => {
    if (isEntityFolder(item)) accum[item.id] = item;
    return accum;
  }, {});
  return data.filter(d => visibleSitesById[d.id]);
};

const AreaChart = ({ areaData, visibleItems, hoveredItem, onHoverPieChartItem, isLoading }: AreaDataProps) => {
  const [entityName, data = []] = areaData ? Object.entries(areaData)[0] : ['', []];

  const visibleData = getVisibleData(data, visibleItems);
  const pieData = visibleData
    .map(entity => ({
      x: entity.id,
      y: parseFloat(entity.netArea.toFixed(1)),
    }))
    .sort((a, b) => b.y - a.y);

  const renderContent = () => {
    if (isLoading) return <LoadingIndicator />;
    if (pieData.length === 0) return <p className="empty-net-area">No data available</p>;

    return (
      <PieChart
        animate={true}
        data={pieData}
        innerRadius={({ datum }) => {
          if (Number(datum?.x) === Number(hoveredItem?.id)) {
            return HIGHLIGHTED_SLICE_INNER_RADIUS;
          }
          return DEFAULT_PIE_INNER_RADIUS;
        }}
        colorFunction={dataSource => getChartColor(dataSource, hoveredItem)}
        innerLabel={() => getInnerLabel(entityName, pieData, data, hoveredItem)}
        onMouseOver={dataSource => {
          onHoverPieChartItem(dataSource.datum.x);
          return {
            innerRadius: HIGHLIGHTED_SLICE_INNER_RADIUS,
          };
        }}
        onMouseOut={() => onHoverPieChartItem(undefined)}
        labelStyle={hoveredItem ? { fontSize: '13px' } : { fontSize: '20px' }}
        showLabelByDefault
      />
    );
  };

  return (
    <div className="analysis">
      <p>{capitalize(entityName)} distribution</p>
      {renderContent()}
    </div>
  );
};

export default AreaChart;
