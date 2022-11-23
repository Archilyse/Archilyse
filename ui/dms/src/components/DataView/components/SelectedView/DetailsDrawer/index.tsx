import React, { useState } from 'react';
import { DateUtils, Editable, Widget } from 'archilyse-ui-components';
import { ItemIcon, Tags } from 'Components';
import { C } from 'Common';
import { useRouter } from 'Common/hooks';
import { inView } from '../../../modules';
import { useStore } from '../../../hooks';
import { WIDGETS_TABS } from '../widgets';
import Comments from './Comments';
import AreaChart from './AreaChart';
import './detailsDrawer.scss';

const DRAWER_ICON_STYLE = {
  fontSize: '50px',
};
const { FLOORS, BUILDINGS, UNITS, ROOMS, SITES } = C.DMS_VIEWS;

const insideAClient = pathname => inView([SITES, BUILDINGS, FLOORS, UNITS, ROOMS], pathname);

const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) {
    return '0 Bytes';
  }
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const Details = ({ details, onDownload, onChange, onRenameFile, onDelete }) => {
  const [editingFileName, setEditingFileName] = useState(false);

  const handleDetailsFileNameSave = newFileName => {
    onRenameFile({ ...details, name: newFileName });
    setEditingFileName(false);
  };

  const handleFileNameClick = () => {
    setEditingFileName(true);
  };

  return (
    <div className="details-tab">
      <div className="details-headers">
        <div className="details-name-type">
          <ItemIcon mimeType={details.type} style={DRAWER_ICON_STYLE} />
          <Editable onSave={handleDetailsFileNameSave} value={details.name} editing={editingFileName}>
            <h3 onDoubleClick={handleFileNameClick}>{details.name}</h3>
          </Editable>
        </div>
        <div className="details-summary">
          <div className="details-row">
            <div>Size</div>
            {formatBytes(details.size)}
          </div>
          {details.updated && (
            <div className="details-row">
              <div>Modified</div>
              {DateUtils.getFullDateFromISOString(details.updated)}
            </div>
          )}
          <div className="details-row">
            <div>Created</div>
            {DateUtils.getFullDateFromISOString(details.created)}
          </div>
        </div>
      </div>
      <div key="details-labels">
        <Tags
          value={details.labels}
          suggestions={details.labels}
          onChange={(event, value) => onChange({ ...details, labels: value }, { reload: true })}
          editable={true}
        />
      </div>
      <div className="details-actions">
        <button className="default-button details-download-button" onClick={() => onDownload(details)}>
          Download
        </button>
        <button className="default-button details-delete-button" onClick={() => onDelete(details)}>
          Delete
        </button>
      </div>
    </div>
  );
};

const getTabs = (pathname, details): [string[], number] => {
  const tabs = [];
  let initialTab = 0;
  const showAnalysisTab = insideAClient(pathname);
  if (showAnalysisTab) tabs.push(WIDGETS_TABS.DASHBOARD);
  if (details) {
    tabs.push(WIDGETS_TABS.DETAILS, WIDGETS_TABS.COMMENTS);
    initialTab = showAnalysisTab ? 1 : 0;
  }
  return [tabs, initialTab];
};

const DetailsDrawer = ({
  areaData = null,
  isAreaDataLoading,
  details,
  onHoverPieChartItem,
  onChange,
  onRenameFile,
  onDownload,
  onAddComment,
  onDelete,
}) => {
  const { pathname } = useRouter();
  const [tabs, initialTab] = getTabs(pathname, details);
  const hoveredItem = useStore(state => state.hoveredItem);
  const visibleItems = useStore(state => state.visibleItems);
  return (
    <Widget className="details-drawer" initialTab={initialTab} tabHeaders={tabs}>
      {tabs.includes(WIDGETS_TABS.DASHBOARD) && (
        <AreaChart
          areaData={areaData}
          isLoading={isAreaDataLoading}
          visibleItems={visibleItems}
          hoveredItem={hoveredItem}
          onHoverPieChartItem={onHoverPieChartItem}
        />
      )}
      {details && (
        <Details
          onRenameFile={onRenameFile}
          details={details}
          onChange={onChange}
          onDownload={onDownload}
          onDelete={onDelete}
        />
      )}
      {details && <Comments comments={details.comments} onAddComment={comment => onAddComment(details, comment)} />}
    </Widget>
  );
};

export default DetailsDrawer;
