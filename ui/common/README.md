# Archilyse UI Components

This repository holds the package for the common components used across Archilyse UI.

# Usage

0. Install modules: `npm install`

1. Build npm package: `npm run dist`

2. Install the local package in the desired project: `npm install --save ../common/archilyse-ui-components@0.0.1.tar.gz`

3. Import styles (this step be erased in the future).
   `import 'archilyse-ui-components/dist/styles.css';`

4. Import the component:
   `import { Map } from 'archilyse-ui-components`

## Development

0. Run `npm run dev` for re-building the package automatically everytime the code is changed.

## Makefile recipe

- Develop:

`make run_ui_common_library`

- Build the package:

`make setup_components_library`
