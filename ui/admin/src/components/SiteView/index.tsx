import React, { useContext, useEffect, useState } from 'react';
import XLSX from 'xlsx/xlsx.mini';
import { parse as parseCSV } from 'papaparse';
import SiteModel from 'Common/types/models/Site';
import { getFile } from 'Common/modules';
import { Button, Link } from '@material-ui/core';
import { SnackbarContext } from 'archilyse-ui-components';
import removeFalsy from 'Common/modules/removeFalsy';
import EntityView from '../EntityView';
import Table from '../Table';
import Tabs from '../Tabs';
import formFields from '../../common/forms/site';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';
import SiteMap from './SiteMap';
import './siteView.scss';

const { CSV, EXCEL_OLD, EXCEL_NEW } = C.MIME_TYPES;

const QaTemplateRenderer = () => {
  const onClick = async () => {
    const response = await ProviderRequest.getFiles(C.URLS.QA_TEMPLATE(), C.RESPONSE_TYPE.TEXT);
    await getFile(response, `template.csv`, C.MIME_TYPES.CSV);
  };
  return (
    <Link href="#" onClick={onClick}>
      QA Template
    </Link>
  );
};

// @TODO: Move to its own file
const TableSheet = ({ onTableReady, initialRows = [] }) => {
  const [uploadedRows, setUploadedRows] = useState([]);
  let selectedFile;

  const handleFile = (file: File) => {
    if (!file) return;

    const reader = new FileReader();
    const rABS = !!reader.readAsBinaryString;
    reader.onload = e => {
      const bstr: any = e.target.result;
      let rows;
      if (file.type === CSV) {
        const result = parseCSV(bstr, { header: true });
        rows = result.data;
      } else {
        const wb = XLSX.read(bstr, { type: rABS ? 'binary' : 'array', raw: true });
        const [firstSheetName] = wb.SheetNames;
        const ws = wb.Sheets[firstSheetName];
        rows = XLSX.utils.sheet_to_json(ws);
      }
      setUploadedRows(rows);
    };

    if (rABS) reader.readAsBinaryString(file);
    else reader.readAsArrayBuffer(file);
  };

  const onChangeFile = event => {
    const files = event.target.files;
    selectedFile = files && files[0];
    handleFile(selectedFile);
  };
  const columns = Object.keys(uploadedRows[0] || {}).map(columnName => {
    return {
      headerName: columnName,
      field: columnName,
      resizable: true,
      filter: true,
      sortable: true,
      editable: true,
    };
  });

  useEffect(() => {
    if (uploadedRows.length === 0) {
      setUploadedRows(initialRows);
    }
  }, [initialRows]);

  return (
    <>
      <div className="table-qa-actions">
        <input
          type="file"
          name="qa_file"
          accept={`${CSV},${EXCEL_OLD},${EXCEL_NEW}`}
          id="qa_file"
          onChange={onChangeFile}
        />
        <QaTemplateRenderer />
      </div>
      {uploadedRows.length > 0 && (
        <div className="table-qa-container">
          <Table id={'site_qa_table'} columns={columns} onTableReady={onTableReady} rows={uploadedRows} />
        </div>
      )}
    </>
  );
};

const parseTableData = QAData => {
  QAData = QAData || [];
  return Object.keys(QAData).map(clientId => {
    const clientData = QAData[clientId];
    return { apartment_client_id: clientId, ...clientData };
  });
};

const parseQAData = tableData => {
  const rowIsNotEmpty = row => Object.values(row).some(value => value);
  return tableData.filter(rowIsNotEmpty).reduce((accum, row) => {
    const { apartment_client_id, ...rest } = row;
    accum[apartment_client_id] = rest;
    return accum;
  }, {});
};

const IfcStatus = ({ site }: { site: SiteModel }) => {
  const rows = [{ status: site?.ifc_import_status, exceptions: site?.ifc_import_exceptions }];
  return (
    <>
      <div className="ifc-status-container">
        {rows[0].status ? <p>Status: {rows[0].status}</p> : 'IFC file has not been added to this site'}
        {rows[0].exceptions ? (
          <p>
            Errors: {rows[0].exceptions['code']}, {rows[0].exceptions['msg']}
          </p>
        ) : (
          ''
        )}
      </div>
    </>
  );
};

const SiteJobs = ({ site, snackbar }) => {
  const taskMap = [
    {
      endpoint: C.ENDPOINTS.SITE_TASK_ALL_DELIVERABLES,
      description: 'Generate All Deliverables',
    },
    {
      endpoint: C.ENDPOINTS.SITE_TASK_GENERATE_IFC_FILE_TASK,
      description: 'Generate IFC',
    },
    {
      endpoint: C.ENDPOINTS.SITE_TASK_GENERATE_UNIT_PLOTS_TASK,
      description: 'Generate Benchmark Charts',
    },
    {
      endpoint: C.ENDPOINTS.SITE_TASK_GENERATE_VECTOR_FILES_TASK,
      description: 'Generate Vector Files',
    },
    {
      endpoint: C.ENDPOINTS.SITE_TASK_GENERATE_ENERGY_REFERENCE_AREA,
      description: 'Generate EBF Summary',
    },
    {
      endpoint: C.ENDPOINTS.SITE_TASK_SLAM_RESULTS_SUCCESS,
      description: 'Force Simulation Status to success',
    },
  ];

  const runTask = async (endpoint, id) => {
    try {
      await ProviderRequest.post(endpoint(id), {});
      snackbar.show({
        message: `Successfully started job for site with id [${id}]`,
        severity: 'success',
      });
    } catch (error) {
      const customMessage = error.response && error.response.data && error.response.data.msg;
      snackbar.show({
        message: customMessage || 'Some requirements are not met for the site requested',
        severity: 'error',
      });
      console.log('Error trying to start job', error);
    }
  };

  const siteId = site.id;
  const jobButton = (endpoint, description) => {
    return (
      <div className="site-jobs-container">
        <Button
          variant="contained"
          className="generate-task-button"
          onClick={async () => await runTask(endpoint, siteId)}
        >
          {description}
        </Button>
      </div>
    );
  };

  return <>{taskMap.map(o => jobButton(o.endpoint, o.description))}</>;
};

const SiteView = ({ parent = undefined, site, qa = undefined, isUpdated = undefined }) => {
  const [coordinates, setCoordinates] = useState({ lat: site.lat || '', lon: site.lon || '' });
  const [table, setTable] = useState<any>();
  const snackbar = useContext(SnackbarContext);

  const defaultQaData = (qa && qa.data) || {};
  let validatedFormFields = formFields;
  if (isUpdated) validatedFormFields = formFields.filter(obj => obj.name !== 'ifc');
  site.lon = String(coordinates.lon);
  site.lat = String(coordinates.lat);

  const clientId = parent ? parent.id : site.client_id;

  const onCreate = async data => {
    const newQaData = getNewQaContent(table);
    const siteQa = await ProviderRequest.post(C.ENDPOINTS.QA(), { client_id: clientId, data: newQaData });

    data.client_id = clientId;
    data.qa_id = siteQa.id;
    removeFalsy(data);

    await ProviderRequest.multipart(C.ENDPOINTS.SITE(), data);

    snackbar.show({ message: 'Created successfully', severity: 'success' });
  };

  const onUpdate = async data => {
    const newQaData = getNewQaContent(table);

    delete data.qa_id;
    const clientSiteId = data.client_site_id || site.client_site_id;
    const qaUpdateBody = { data: newQaData, client_id: clientId, site_id: site.id };
    if (clientSiteId) {
      qaUpdateBody['client_site_id'] = clientSiteId;
    }

    const num_clusters = data.sub_sampling_number_of_clusters;
    removeFalsy(data);
    if (!num_clusters) {
      data.sub_sampling_number_of_clusters = null;
    }
    await ProviderRequest.put(C.ENDPOINTS.QA(qa.id), qaUpdateBody);
    await ProviderRequest.put(C.ENDPOINTS.SITE_BY_ID(site.id), data);
    snackbar.show({ message: 'Updated successfully', severity: 'success' });
  };

  const getNewQaContent = table => {
    if (table) {
      //User entered data on QA tab
      const tableData = [];
      table.forEachNode(node => tableData.push(node.data));
      return parseQAData(tableData);
    }
    return defaultQaData;
  };

  const onChange = formValues => {
    setCoordinates({ lat: formValues.lat, lon: formValues.lon });
  };

  const onMapLocationSelected = mapValues => {
    setCoordinates({ lat: mapValues.lat, lon: mapValues.lon });
  };

  const onTableReady = params => {
    setTable(params.api);
  };

  return (
    <>
      <Tabs headers={['General', 'QA', 'IFC Status', 'Jobs']}>
        <div className="site-general">
          <EntityView
            fields={validatedFormFields}
            entity={site}
            context="site"
            parent={parent}
            parentKey={'client_id'}
            onChange={onChange}
            onCreate={onCreate}
            onUpdate={onUpdate}
          />
          <SiteMap onMapLocationSelected={onMapLocationSelected} coordinates={coordinates} />
        </div>
        <div className="qa">
          <TableSheet onTableReady={onTableReady} initialRows={parseTableData(defaultQaData)} />
        </div>
        <div className="ifc-status" data-testid="ifc-status-tab">
          <IfcStatus site={site} />
        </div>
        <div className="site-jobs" data-testid="site-jobs-tab">
          <SiteJobs site={site} snackbar={snackbar} />
        </div>
      </Tabs>
    </>
  );
};

export default SiteView;
