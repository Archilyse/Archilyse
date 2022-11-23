// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export function getCommonEnvironment(baseUrl) {
  return {
    production: false,

    apiPlanUrl: `${baseUrl}plan/`,
    apiFloorUrl: `${baseUrl}floor/`,
    apiBuildingUrl: `${baseUrl}building/`,
    apiAnnotationUrl: `${baseUrl}annotation/`,
    apiUnitUrl: `${baseUrl}unit/`,
    apiConstantsUrl: `${baseUrl}constants/`,
    apiPotentialUrl: `${baseUrl}potential/`,
    apiFeaturesUrl: `${baseUrl}features/`,
    apiSiteUrl: `${baseUrl}site/`,

    /*
    Platform login
    */
    apiAuthUrl: `${baseUrl}auth/login`,

    apiQaUrl: `${baseUrl}qa/`,

    adminBuildingsUrl: 'https://slam.archilyse.com/admin/pipelines?site_id=',

    googleTrackingId: 'UA-109816142-4',

    mapboxToken: 'pk.eyJ1IjoibGVzejNrIiwiYSI6ImNra3FyMHlmOTBoY28ydXBmc3Vzb2t0cjYifQ.PGuiWX9XwpBkCgC6FdbceA',

    sentryDSN: '', // Disabled in development

    /** Display detailed errors in the console, for debug only */
    displayErrors: true,

    /** QA error detecting parameters */
    qaErrorMarginM2: 0.02,
    qaErrorMarginRooms: 0,

    /** dashboardURL */
    dashboardURL: 'http://localhost:8080',
  };
}

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
import 'zone.js/dist/zone-error'; // Included with Angular CLI.
