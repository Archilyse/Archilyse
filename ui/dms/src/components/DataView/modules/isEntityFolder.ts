const ENTITY_FOLDER = 'folder-';

export default entity => entity?.type && entity.type.includes(ENTITY_FOLDER);
