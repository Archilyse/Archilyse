import numpy as np

from common_utils.constants import ADMIN_SIM_STATUS


def response_message(response):
    return f"Error code: {response.status_code}. Text: {response.data}"


def get_vtk_mesh_vertices(mesh):
    vertices = mesh.GetPoints()
    vertex_array = vertices.GetData()

    return np.array(
        [
            [vertex_array.GetComponent(i, j) for j in range(3)]
            for i in range(vertices.GetNumberOfPoints())
        ]
    )


def get_vtk_mesh_faces(mesh):
    import vtk

    faces = []
    for i in range(mesh.GetNumberOfCells()):
        face = vtk.vtkIdList()
        mesh.GetCellPoints(i, face)
        faces.append([face.GetId(j) for j in range(3)])

    return np.array(faces)


def generate_icosphere(radius, center, refinement_order=0):
    import vtk

    icoSource = vtk.vtkPlatonicSolidSource()
    icoSource.SetSolidTypeToIcosahedron()
    icoSource.Update()

    smooth_loop = vtk.vtkLoopSubdivisionFilter()
    smooth_loop.SetNumberOfSubdivisions(refinement_order)
    smooth_loop.SetInputConnection(icoSource.GetOutputPort())
    smooth_loop.Update()

    transform = vtk.vtkTransform()
    transform.Translate(*center)
    transform.Scale(radius / 0.701, radius / 0.701, radius / 0.701)
    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputConnection(smooth_loop.GetOutputPort())
    transform_filter.SetTransform(transform)
    transform_filter.Update()

    return transform_filter.GetOutput()


def generate_box(corner1, corner2):
    import vtk

    p1, p2 = np.array(corner1), np.array(corner2)
    diagonal = p2 - p1

    cuboidSource = vtk.vtkCubeSource()
    cuboidSource.SetCenter(*(p1 + diagonal / 2))
    cuboidSource.SetXLength(diagonal[0])
    cuboidSource.SetYLength(diagonal[1])
    cuboidSource.SetZLength(diagonal[2])
    cuboidSource.Update()

    return cuboidSource.GetOutput()


def add_site_permissions(site_id, user_id, permission_type: str):
    from handlers.db import DmsPermissionDBHandler

    DmsPermissionDBHandler.add(
        site_id=site_id,
        user_id=user_id,
        rights=permission_type,
    )


def change_site_ownership(site_id, client_id):
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(item_pks={"id": site_id}, new_values={"client_id": client_id})


def assert_site_consistency(site_id: int, consistency_altered: bool):
    from handlers.db import SiteDBHandler

    # Make sure consistency is not affected by adding tags to entities
    updated_site = SiteDBHandler.get_by(id=site_id)
    assert updated_site["pipeline_and_qa_complete"] is not consistency_altered
    assert updated_site["heatmaps_qa_complete"] is not consistency_altered
    status_expected = (
        ADMIN_SIM_STATUS.SUCCESS.value
        if consistency_altered is False
        else ADMIN_SIM_STATUS.UNPROCESSED.value
    )
    for task_field in [
        "basic_features_status",
        "full_slam_results",
        "sample_surr_task_state",
    ]:
        assert updated_site[task_field] == status_expected, task_field
