import { FloorplanEditorLib } from './floorplan-editor-lib';
import { EditorConstants } from '../../_shared-libraries/EditorConstants';

describe('Floorplan editor library', () => {
  it('should concatenate visible groups', () => {
    const objectsInitial = [
      {
        id: 'object 1',
      },
      {
        id: 'object 2',
      },
    ];
    const group = {
      visible: true,
      type: EditorConstants.THREEJS_GROUP,
      children: [
        {
          type: EditorConstants.THREEJS_MESH, // This one WOULD! be included
        },
        {
          visible: false, // <- NOT visible
          type: EditorConstants.THREEJS_GROUP,
          children: [
            {
              type: EditorConstants.THREEJS_MESH, // This one won't be included
            },
          ],
        },
      ],
    };

    const onlyAreasOrWalls = false;

    const result = FloorplanEditorLib.concatIfVisibleGroupOfGroups(objectsInitial, group, onlyAreasOrWalls);

    expect(result).toBeDefined();
    expect(result).not.toBeNull();
    expect(result.length).toBe(3);
  });
});
