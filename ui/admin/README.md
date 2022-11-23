# Admin UI

This folder contains the admin user interface for the SLAM repo as well as the Document Management System app (DMS).

## Pre-requisites

Assuming you are in the correct directory in the slam repo (`/slam/ui/admin`), install dependencies by running:

`npm install`

Then add to your `.local-env` file in `/slam/docker` the following:

```
FLOORPLAN_UPLOAD_DIR=/tmp
```

## Development

To launch a development server with hot reload, type:

`npm run dev`

And go to: [`http://localhost:4000/admin`](http://localhost:4000/admin)

## Production

Generate the production assets by running:

`npm run build`

And then launch a server to serve those assets:

`npm run start`

The production app will be located in:
[`http://localhost/admin`](http://localhost/admin)

In production environment, the app should be under:

[`http://app.archilyse.com/admin`](`http://app.archilyse.com/admin)

## Tests

Run snapshot tests by typing:

`npm run test`

In case any snapshot must be updated, type:

`npm run test -- u`

## Folder structure

- `common`: Constants and common elements between the rest of the app.
- `components`: Directory of common components used in the rest of the app.

  If a component is made of other, smaller components, it will be in a folder with the same name, e.g.:

```
 BigComponent/
 ├── smallerComponent1.scss
 ├── smallerComponent1.tsx
 ├── smallerComponent2.scss
 ├── smallerComponent2.tsx
 ├── index.tsx

```

Having the main component in `index.tsx`.

- `views`: Directory of "views", every file here reprsents a specific view in the app.
- `providers`: Wrappers to external libraries. Therefore, instead of using a library directly in the code we built a wrapper that abstract its internals.
- `assets`: Public resources (images, fonts..).
- `tests` : Unit & Snapshot tests

## Tech stack

Built using [`React`](https://reactjs.org/) using [React Hooks](https://reactjs.org/docs/hooks-intro.html), [`ag-grid`](https://www.ag-grid.com/) and [Material UI](https://material-ui.com/).
