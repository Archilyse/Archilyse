import React from 'react';
import useSWR from 'swr';
import GoToCompetitionToolRenderer from 'Components/GoToCompetitionToolRenderer';
import { Admin, LinkRenderer } from '../components';
import { ProviderRequest } from '../providers';
import { C } from '../common';
import { useRouter } from '../common/hooks';

const getColumns = () => {
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
      headerName: '',
      field: 'edit',
      cellRendererFramework: ({ data }) => <LinkRenderer id={data.id} href={`/competition/${data.id}`} text={'Edit'} />,
      width: 70,
    },
    {
      headerName: '',
      field: 'features_selection',
      cellRendererFramework: ({ data }) => (
        <LinkRenderer id={data.id} href={`/competition/${data.id}/features`} text={'Features Selection'} />
      ),
      width: 70,
    },
    {
      headerName: '',
      field: 'competition_config',
      cellRendererFramework: ({ data }) => (
        <LinkRenderer id={data.id} href={`/competition/${data.id}/config`} text={'Configuration'} />
      ),
      width: 70,
    },
    {
      headerName: '',
      field: 'link_to_competition_tool',
      cellRendererFramework: GoToCompetitionToolRenderer,
      width: 70,
    },
  ];
  columns = columns.map(c => ({
    filter: true,
    sortable: true,
    resizable: true,
    ...c,
  }));
  return columns;
};

const Competitions = () => {
  const { query } = useRouter();
  const { data: competitions } = useSWR(C.ENDPOINTS.COMPETITIONS_BY_CLIENT(query.client_id), ProviderRequest.get);
  const columns = getColumns();
  return (
    <Admin
      rows={competitions}
      id={'competitions_table'}
      columns={columns}
      allowCreation
      parentFilter={`client_id=${query.client_id}`}
    />
  );
};

export default Competitions;
