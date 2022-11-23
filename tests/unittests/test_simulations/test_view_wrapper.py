from unittest.mock import call

import pytest

from common_utils.exceptions import QuavisSimulationException


def test_generate_quavis_input_should_validate_output_filename_format(mocker):
    from numpy import array

    from simulations.view import ViewWrapper

    mock_antiglitch_translation = mocker.patch.object(
        ViewWrapper, "_anti_gpu_glitch_translation"
    )
    mock_input_scene_objects = mocker.patch.object(ViewWrapper, "_input_scene_objects")
    mock_input_observation_points = mocker.patch.object(
        ViewWrapper, "_input_observation_points"
    )
    view_wrapper = ViewWrapper()
    view_wrapper._mean_pos = array((0, 0, 0))
    quavis_input = view_wrapper.generate_input(
        run_volume=True, run_sun=True, run_area=True
    )
    output_path = quavis_input["quavis"]["output"]["filename"]
    assert output_path is not None
    assert output_path.startswith(view_wrapper._quavis_io_base_dir.as_posix())
    assert output_path.endswith(".out.json")
    assert quavis_input["quavis"]["header"]["name"] in output_path

    mock_antiglitch_translation.assert_called_once()
    mock_input_scene_objects.assert_called_once()
    mock_input_observation_points.assert_called_once()


def test_execute_quavis(mocker, quavis_input):
    import json
    from pathlib import Path

    from simulations.view import ViewWrapper

    path_open = mocker.mock_open()

    def intercept_pathlib_open_args(self, *args, **kwargs):
        return path_open(self, *args, **kwargs)

    mocker.patch.object(Path, "open", intercept_pathlib_open_args)
    mocker.patch.object(Path, "unlink")
    json_dump_mock = mocker.patch.object(json, "dump")
    json_load_mock = mocker.patch.object(json, "load")
    delegator_mock = mocker.patch("simulations.view.view_wrapper.delegator")
    delegator_mock.run.return_value.err = None
    delegator_mock.run.return_value.out = "Done"
    delegator_mock.run.return_value.return_code = 0

    view_wrapper = ViewWrapper()
    view_wrapper.execute_quavis(quavis_input=quavis_input)

    expected_output_path = Path(quavis_input["quavis"]["output"]["filename"])
    expected_input_path = Path(
        str(expected_output_path).replace(
            "".join(expected_output_path.suffixes), ".in.json"
        )
    )

    delegator_mock.run.assert_called_once_with(
        f"{view_wrapper._quavis_bin_location.as_posix()} {expected_input_path.as_posix()}",
        block=True,
    )

    assert call(expected_input_path, "w") in path_open.mock_calls
    assert call(expected_output_path) in path_open.mock_calls
    json_dump_mock.assert_called_once()
    json_load_mock.assert_called_once()


def test_execute_quavis_raises_exception(mocker, quavis_input):
    from pathlib import Path

    from simulations.view import ViewWrapper

    path_open = mocker.mock_open()

    def intercept_pathlib_open_args(self, *args, **kwargs):
        return path_open(self, *args, **kwargs)

    mocker.patch.object(Path, "open", intercept_pathlib_open_args)
    mocker.patch.object(Path, "unlink")
    delegator_mock = mocker.patch("simulations.view.view_wrapper.delegator")
    delegator_mock.run.return_value.err = None
    delegator_mock.run.return_value.out = "Segmentation fault or something alike"
    delegator_mock.run.return_value.return_code = 139

    view_wrapper = ViewWrapper()
    with pytest.raises(QuavisSimulationException):
        view_wrapper.execute_quavis(quavis_input=quavis_input)


def test_load_wrapper_from_quavis_input(
    mocker, quavis_output__test_load_wrapper_from_quavis_input
):
    import json

    import numpy as np

    from simulations.view import ViewWrapper

    # some metadata used for generating the test scene
    np.random.seed(42)
    N_obs = 10
    N_solar_times = 4
    N_geoms = 1000
    N_groups = 3

    # now we initialize the wrapper with obs points and geometry
    wrapper = ViewWrapper(resolution=16)
    observation_points = np.random.rand(N_obs, 3)
    view_directions = np.random.rand(N_obs, 3)
    fovs = np.random.rand(N_obs) * 360.0
    solar_pos = np.random.rand(N_obs, N_solar_times, 2) * 2 * np.pi
    solar_zenith_values = np.random.rand(N_obs, N_solar_times)

    for i in range(N_obs):
        wrapper.add_observation_point(
            pos=observation_points[i].tolist(),
            view_direction=view_directions[i].tolist(),
            fov=fovs[i].tolist(),
            solar_pos=[tuple(x.tolist()) for x in solar_pos[i]],
            solar_zenith_luminance=solar_zenith_values[i].tolist(),
        )

    for i in range(N_groups):
        wrapper.add_triangles(
            np.random.rand(N_geoms // N_groups, 3, 3).tolist(), group=str(i)
        )

    # now we generate the quavis input from the original wrapper and load a new wrapper from the input
    quavis_input = wrapper.generate_input(run_area=True, run_volume=True, run_sun=True)
    loaded_wrapper = ViewWrapper.load_wrapper_from_input_no_geometries(
        input_data=quavis_input
    )

    # if the original wrapper and the loaded wrapper parse the output file the same, it works
    assert json.dumps(
        wrapper.parse_quavis_output(quavis_output__test_load_wrapper_from_quavis_input)
    ) == json.dumps(
        loaded_wrapper.parse_quavis_output(
            quavis_output__test_load_wrapper_from_quavis_input
        )
    )
