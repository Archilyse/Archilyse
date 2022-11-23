import KML from 'ol/format/KML';
import { get as getProjection } from 'ol/proj';
import { saveData } from './Url';

/**
 * Helper class to export Kml files
 */
export class KmlExport {
  /** API Layout object */
  layout;
  /** Layout to Building address */
  address;

  /** Selected simulation */
  currentSimulation;

  /** Feature to draw */
  feature;

  /** Detail map layer to take the elements from */
  globalSource;

  /** Map view */
  view;

  /** height to the ground */
  height;
  /** height to the sea */
  absolute_height;

  /**
   * Exports a kml File.
   */
  export(drawSimulation, name, sim_result_categories) {
    // We save the current simulation because it's going to be changed , and then restored
    const originalSimulation = this.currentSimulation;

    const content = this.prepareSimulationsToExport(drawSimulation, name, sim_result_categories, originalSimulation);
    saveData('Archilyse.kml', content);

    // Revert to the original simulation:
    this.currentSimulation = originalSimulation;
    drawSimulation(this.feature);
  }

  /**
   * We navigate through the simulations to build the content.
   * @param drawSimulation
   * @param name
   * @param sim_result_categories
   * @param originalSimulation
   */
  prepareSimulationsToExport(drawSimulation, name, sim_result_categories, originalSimulation) {
    const introduction = `<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Document>
            <name>${name}</name>
            <open>1</open>
            <description> ${this.address} </description>`;

    let content = '';

    const extraFolders = true;

    for (let i = 0; i < sim_result_categories.length; i += 1) {
      this.currentSimulation = sim_result_categories[i];

      // There's no need from extra folder
      let contentFolder = extraFolders ? `<Folder><name>Simulation ${this.currentSimulation}</name>` : ``;

      // Only the original simulation is visible by default
      if (this.currentSimulation !== originalSimulation) {
        contentFolder += `<visibility>0</visibility>`;
      }

      drawSimulation(this.feature);
      const result = this.prepareCurrentSim();
      if (i === 0) {
        content += result.camera;
      }
      contentFolder += result.data;

      if (extraFolders) {
        contentFolder += `</Folder>`;
      }

      content += contentFolder;
    }

    const end = `
        </Document>
    </kml>`;

    return introduction + content + end;
  }

  /**
   * Export only one simulation
   * this.currentSimulation has to be loaded in the map so we can access the DOM from the this.globalSource
   */
  prepareCurrentSim() {
    const format = new KML();
    const features = this.globalSource.getFeatures();

    const result = format.writeFeaturesNode(features, {
      featureProjection: this.view.getProjection(),
      dataProjection: getProjection('EPSG:4326'),
    });

    const documents = result.childNodes[0];
    const featureLists = documents.childNodes;

    const absolute_height = this.absolute_height;
    const heightStrSpace = `,${absolute_height} `;
    const heightStr = `,${absolute_height}`;

    const placemarks = [];
    const center = this.prepareFeatureFromSim(placemarks, featureLists, heightStrSpace, heightStr);

    const lookAt = `<LookAt>
            <longitude>${center[0]}</longitude><latitude>${center[1]}</latitude>
            <altitude>${this.absolute_height}</altitude><heading>0</heading><tilt>50</tilt><range>30</range>
          </LookAt>`;

    return {
      camera: lookAt,
      data: `<Folder><name>${this.currentSimulation} simulation</name>
          <description> Analyzes the ${this.currentSimulation} visibility </description>${lookAt}${placemarks}
         </Folder>`,
    };
  }

  /**
   *
   * @param placemarks
   * @param featureLists
   * @param heightStrSpace
   * @param heightStr
   */
  prepareFeatureFromSim(placemarks, featureLists, heightStrSpace, heightStr) {
    let center = null;
    featureLists.forEach(feature => {
      const featureXML = feature.childNodes;
      const style = featureXML[0];
      const polygon = featureXML[1];

      const XXX = polygon.childNodes[0];
      const YYY = XXX.childNodes[0];
      const coordinateTag = YYY.childNodes[0];
      const coordinates = coordinateTag.childNodes[0];
      const coords = coordinates.nodeValue.split(' ');
      const coordinatesStr = coords.join(heightStrSpace) + heightStr;

      const hexagonColor = style.childNodes[0].childNodes[0].childNodes[0].data;

      const hexagonColorXML = `<color>${hexagonColor}</color>`;
      const styleXML = `<Style><LineStyle>${hexagonColorXML}</LineStyle><PolyStyle>${hexagonColorXML}<fill>1</fill></PolyStyle></Style>`;
      const coordinatesXML = `<outerBoundaryIs><LinearRing><coordinates>${coordinatesStr}</coordinates></LinearRing></outerBoundaryIs>`;
      const polygonXML = `<Polygon><altitudeMode>absolute</altitudeMode>${coordinatesXML}</Polygon>`;

      // Documentation:
      // https://developers.google.com/kml/documentation/kmlreference#polystyle
      placemarks.push(`
        <Placemark>${styleXML}${polygonXML}</Placemark>`);

      if (center === null) {
        center = coords[0].split(',');
      }
    });
    return center;
  }
}
