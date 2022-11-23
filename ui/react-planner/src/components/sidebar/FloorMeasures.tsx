import React from 'react';
import { LoadingIndicator } from 'archilyse-ui-components';
import { convertPixelsToCMs, getLineDistance, getScaleAreaSize, isLine, isPolygon } from '../../utils/geometry';
import { RequestStatusType } from '../../constants';
import { FloorScale, XYCoord } from '../../types';

const STYLE_FLOOR_SCALES: any = {
  display: 'flex',
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'space-between',
};

const STYLE_LOADING: any = { width: 25, height: 25 };

type FloorMeasuresProps = {
  floorScales: FloorScale[];
  points: XYCoord[];
  requestStatus: { status: typeof RequestStatusType[keyof typeof RequestStatusType]; error: string };
};

const MeasureInfo = ({ floorScale, points }) => {
  let lengthInCm;
  let unit;

  if (isLine(points)) {
    const distanceInPx = getLineDistance(points);
    lengthInCm = convertPixelsToCMs(floorScale.scale, distanceInPx);
    unit = <label>m</label>;
  } else if (isPolygon(points)) {
    const areaSizeInPx = getScaleAreaSize(points);
    lengthInCm = floorScale.scale * areaSizeInPx;
    unit = (
      <label>
        m<sup>2</sup>
      </label>
    );
  } else {
    return null;
  }

  return (
    <div style={STYLE_FLOOR_SCALES}>
      <label>
        Floor: {floorScale.floorNumber} - ({floorScale.planId}):
      </label>
      {floorScale.error ? (
        <label>Error fetching info</label>
      ) : (
        <label>
          {lengthInCm.toFixed(2)} {unit}
        </label>
      )}
    </div>
  );
};

const FloorMeasures = ({ floorScales, points, requestStatus }: FloorMeasuresProps) => {
  const isLoading = requestStatus.status === RequestStatusType.PENDING;

  if ((requestStatus.status === RequestStatusType.FULFILLED && !floorScales?.length) || !points?.length) {
    return null;
  }
  return (
    <div style={{ width: '90%', textAlign: `${isLoading ? 'center' : 'left'}` as 'center' | 'left' }}>
      <br />
      <hr />
      <br />
      {isLoading ? (
        <>
          <p>Loading comparison with other floors...</p>
          <LoadingIndicator style={STYLE_LOADING} />
        </>
      ) : (
        <>
          <p>Same {isLine(points) ? 'line' : 'polygon'} in: </p>
          {floorScales.map(floorScale => (
            <MeasureInfo key={floorScale.floorNumber} floorScale={floorScale} points={points} />
          ))}
        </>
      )}
    </div>
  );
};

export default FloorMeasures;
