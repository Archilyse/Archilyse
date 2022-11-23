import isSiteSimulated from './isSiteSimulated';

export default site => isSiteSimulated(site) && site?.heatmaps_qa_complete;
