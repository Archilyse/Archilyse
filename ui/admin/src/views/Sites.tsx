import React from 'react';
import useSWR from 'swr';
import { makeStyles } from '@material-ui/core/styles';
import { auth } from 'archilyse-ui-components';
import { checkAccess } from 'Common/roles';
import { Admin, BooleanRenderer, LinkRenderer, SiteRenderers, StatusRenderer } from '../components';
import { ProviderRequest } from '../providers';
import { isSiteSimulated } from '../common/modules';
import { C } from '../common';
import { useRouter } from '../common/hooks';
import { GetSitesResponse } from '../common/types';

const SMALL_SCREEN_WIDTH = 1500;
const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 500,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

let table;

const expandColumns = columnApi => {
  const allColumnIds = [];
  columnApi.getAllColumns().forEach(column => {
    allColumnIds.push(column.colId);
  });
  columnApi.autoSizeColumns(allColumnIds);
};

const onTableReady = params => {
  table = params;
  if (window.innerWidth < SMALL_SCREEN_WIDTH) {
    expandColumns(params.columnApi);
  }
};

const isColumnHiddenNonAdmin = (data, roles) => data.delivered === true && !roles.includes(C.ROLES.ADMIN);

const getColumns = (cellRenderers, roles) => {
  const {
    GenerateFeaturesRenderer,
    MarkAsDeliveredRenderer,
    DownloadZipRenderer,
    GroupSelectorRenderer,
    ClassificationSchemeSelectorRenderer,
    CustomValuatorRenderer,
  } = cellRenderers;

  let columns: any = [
    {
      headerName: 'ID',
      field: 'id',
      filter: 'agNumberColumnFilter',
      headerClass: 'site_id',
      maxWidth: 55,
    },
    {
      headerName: 'Name',
      field: 'name',
      headerClass: 'site_name',
    },
    {
      headerName: 'Client Site Id',
      field: 'client_site_id',
      headerClass: 'client_site_id',
      maxWidth: 190,
    },
    {
      headerName: 'Region',
      field: 'region',
      maxWidth: 150,
    },
    {
      headerName: 'Lab',
      field: 'ready',
      cellRendererFramework: BooleanRenderer,
      maxWidth: 50,
      headerTooltip: 'Labelled',
    },
    {
      headerName: 'P+QA',
      field: 'pipeline_and_qa_complete',
      cellRendererFramework: BooleanRenderer,
      maxWidth: 60,
      headerTooltip: 'Pipeline + QA',
    },
    {
      headerName: 'BF QA',
      field: 'qa_link',
      cellRendererFramework: ({ data }) => {
        if (!data.ready) {
          return <p title={C.TOOLTIPS.QA}>QA</p>;
        }
        return (
          <a target="_blank" rel="noreferrer" href={`/quality/${data.id}`}>
            QA
          </a>
        );
      },
      maxWidth: 60,
      headerTooltip: 'Basic Features QA',
    },
    {
      headerName: 'Sim',
      field: 'full_slam_results',
      cellRendererFramework: StatusRenderer,
      resizable: true,
      maxWidth: 110,
      headerTooltip: 'Simulated',
    },
    {
      headerName: 'Heat QA',
      field: 'heatmaps_qa_complete',
      cellRendererFramework: BooleanRenderer,
      maxWidth: 70,
      headerTooltip: 'Heatmaps reviewed QA',
    },
    {
      headerName: 'Pipelines',
      field: 'pipelines',
      cellRendererFramework: ({ data }) => {
        if (isColumnHiddenNonAdmin(data, roles)) {
          return <p title={C.TOOLTIPS.PIPELINES}>Pipelines</p>;
        }
        return <LinkRenderer id={data.id} href={`/pipelines?site_id=${data.id}`} text={'Pipelines'} />;
      },
      maxWidth: 85,
      headerTooltip: C.TOOLTIPS.PIPELINES,
    },
  ];

  if (checkAccess('run_simulations')) {
    columns.push({
      headerName: 'Analysis',
      field: 'run_analysis',
      cellRendererFramework: GenerateFeaturesRenderer,
      maxWidth: 100,
    });
  }
  if (roles && roles.includes(C.ROLES.ADMIN)) {
    columns.push(
      {
        headerName: 'ClassScheme',
        field: 'classification_scheme',
        cellRendererFramework: ClassificationSchemeSelectorRenderer,
        maxWidth: 140,
      },
      {
        headerName: 'Heat & Sims',
        field: 'simulations',
        cellRendererFramework: ({ data }) => {
          if (!isSiteSimulated(data)) {
            return <p title={C.TOOLTIPS.SIMULATIONS}>Heat & Sims</p>;
          }
          return (
            <a target="_blank" rel="noreferrer" href={`/dashboard/qa/${data.id}`}>
              Heat & Sims
            </a>
          );
        },
        maxWidth: 140,
        headerTooltip: C.TOOLTIPS.SIMULATIONS,
      },
      {
        headerName: 'Deliverbl.',
        field: 'zip',
        cellRendererFramework: DownloadZipRenderer,
        maxWidth: 80,
      },
      {
        headerName: 'Group',
        field: 'group',
        cellRendererFramework: GroupSelectorRenderer,
        minWidth: 140,
        comparator: (valueA, valueB, nodeA, nodeB) => {
          if (nodeA.data && nodeB.data) {
            return nodeA.data.group_id - nodeB.data.group_id;
          }
          return 0;
        },
      },
      {
        headerName: 'Delivered',
        field: 'delivered',
        cellRendererFramework: MarkAsDeliveredRenderer,
        sortable: true,
        comparator: (valueA, valueB) => valueA - valueB,
        maxWidth: 80,
      },
      {
        headerName: 'P. Hubble',
        filter: false,
        sortable: false,
        minWidth: 200,
        cellRendererFramework: CustomValuatorRenderer,
      },
      {
        headerName: '',
        field: 'actions',
        filter: false,
        sortable: false,
        cellRendererFramework: ({ data }) => (
          <LinkRenderer id={`[data.id]-action`} href={`/site/${data.id}`} text={'Edit'} />
        ),
        maxWidth: 50,
      },
      {
        headerName: '',
        field: 'surroundings',
        filter: false,
        sortable: false,
        cellRendererFramework: ({ data }) => (
          <LinkRenderer id={`${data.id}-action`} href={`/manual_surroundings/${data.id}`} text={'Surroundings'} />
        ),
        maxWidth: 100,
      }
    );
  }
  columns = columns.map(c => ({
    filter: true,
    sortable: true,
    resizable: true,
    ...c,
  }));
  return columns;
};

const getRequestUrl = query => {
  const { client_id = 1, client_site_id = null } = query;
  if (client_site_id) {
    return `${C.ENDPOINTS.SITES_WITH_READY_BY_CLIENT(client_id)}&client_site_id=${client_site_id}`;
  }
  return `${C.ENDPOINTS.SITES_WITH_READY_BY_CLIENT(client_id)}`;
};

const Sites = () => {
  const { query } = useRouter();

  const classes = useStyles();
  const roles = auth.getRoles();
  const { data: sites } = useSWR<GetSitesResponse[]>(getRequestUrl(query), ProviderRequest.get);
  const { data: parent = [] } = useSWR(C.ENDPOINTS.CLIENT(query.client_id), ProviderRequest.get);
  const { data: groups } = useSWR(C.ENDPOINTS.GROUP(), ProviderRequest.get);
  const { data: classificationSchemes } = useSWR(C.ENDPOINTS.CLASSIFICATION_SCHEMES(), ProviderRequest.get);

  // @TODO Do this in data view to avoid flickering and re-rendering <DataView /> all the time
  if (!groups || !classificationSchemes) return null;

  const cellRenderers = SiteRenderers(classes, groups, classificationSchemes);
  const columns = getColumns(cellRenderers, roles);

  return (
    <>
      <Admin
        rows={sites}
        columns={columns}
        onTableReady={onTableReady}
        id={'sites_table'}
        allowCreation
        onExpand={() => expandColumns(table.columnApi)}
        parentFilter={parent ? `client_id=${parent.id}` : ``}
      />
    </>
  );
};

export default Sites;
