# DMS

This folder contains the Document Management System app (DMS).

## Pre-requisites

Assuming you are in the correct directory in the slam repo (`/slam/ui/dms`), install dependencies by running:

`npm install`

## Development

To launch a development server with hot reload, type:

`npm run dev`

And go to: [`http://localhost:4000/dms`](http://localhost:4000/dms)

## Production

Simply go to the slam repo root and execute:

`make up`

The production app will be located in:
[`http://localhost/dms`](http://localhost/dms)

In production environment, the app should be under:

[`http://one.archilyse.com/`](`http://one.archilyse.com/)

## Tests

Run unit & integration tests by typing:

`npm run test`

## Folder structure

- `common`: Constants and common elements between the rest of the app.
- `components`: Directory of common components used in the rest of the app.

  If a component is made of other, smaller components, it will has a `components` with the subcomponents on it:

```
 BigComponent/
 |── components
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
- `tests` : Unit & Integration tests

## Tech stack

Built using [`React`](https://reactjs.org/) using [React Hooks](https://reactjs.org/docs/hooks-intro.html) and [zustand](https://github.com/pmndrs/zustand) as a state manager.
