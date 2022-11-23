import { DMSItem } from 'Common/types';

export const parseDMSSiteItem = (item, type): DMSItem & { clientSiteId: string } => ({
  ...parseDMSItem(item, type),
  clientSiteId: item.client_site_id,
});

export const parseDMSUnitItem = (item, type, netArea = 1): DMSItem & { phPrice: number; phFactor: number } => ({
  ...parseDMSItem(item, type),
  phPrice: item.ph_final_gross_rent_annual_m2 * netArea,
  phFactor: item.ph_final_gross_rent_adj_factor,
});

export const parseDMSFloorItem = (item, type): DMSItem & { phPrice: number; phFactor: number } => ({
  ...parseDMSItem(item, type),
  phPrice: 0,
  phFactor: 0,
});

export const parseDMSItem = (item, type): DMSItem => ({
  id: item.id,
  name: item.name,
  labels: item.labels || [],
  created: item.created,
  updated: item.updated,
  type,
});
