from handlers import FloorHandler


def test_get_georeferencing_transformation_sample_case(
    first_pipeline_complete_db_models, georeference_parameters
):
    floor_info = first_pipeline_complete_db_models["floor"]
    georef = FloorHandler.get_georeferencing_transformation(floor_id=floor_info["id"])
    for k, v in georeference_parameters.items():
        assert getattr(georef, k) == v, k
