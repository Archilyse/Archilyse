"""Wrapper for the CPP view simulation."""
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import delegator
import numpy as np

from common_utils.exceptions import QuavisSimulationException
from common_utils.logger import logger


class ViewWrapper:
    """A wrapper for the CPP view implementation.

    Basic usage is to add triangles of a certain group to the simulation and
    to trigger the `run` method with a given set of observation points.
    Observation points can have a specified view cone (direction of view and
    field of view).

    Example:
        ```
        sim = Wrapper(resolution=64)
        for t in triangles:
            sim.add_triangle(t.A, t.B, t.C, group=triangle.grp)

        for p in observation_points:
            sim.add_observation_point(p.pos, p.fov, p.view_direction)

        view_results = sim.run()
        for idx, result in enumerate(view_results):
            p = observation_points[idx]
            for grp in result['area']:
                print(p, result['simulations']['area_by_group'][grp])
        ```
    """

    # Rendering & Computation Settings
    _sim_resolution = None

    # Maximum Number of Groups
    _MAX_GROUPS: int = 512

    _quavis_bin_location = Path("/usr/bin/quavis")
    _quavis_io_base_dir = Path("/tmp")

    def __init__(self, resolution: int = 128):
        """Initializes the a view simulation.

        Args:
            resolution (int): Defaults to 64. The rendering resolution. Should
                be a power of two.
        """
        # Geometry attributes
        # Triangles added to the view simulation are assigned to groups. Each group
        # has a specific index (0..n) and is member of list _geom_groups.
        # The _geom_triangles attribute is a list of lists where element i of
        # _geom_triangles contains all triangles of group i. Each triangle is stored
        # as a 3-tuple of vertices A, B, C corresponding to the three triangle
        # corners. Each vertex is stored as a 3-tuple as well, corresponding to the
        # vertex coordinates x, y, z.
        self._geom_group_to_index: Dict[str, int] = {}  # grp -> idx
        self._geom_groups: List[str] = []  # idx -> grp
        self._geom_triangles: List[np.ndarray] = []  # idx -> geoms

        # Observation point attributes. Each observation point has a positions
        # with (x, y, z) coordinates using the coordinate system of the triangles
        # stored in _obs_positions.
        #
        # Furthermore, an observation point i has an optional field of view which is
        # represented by single angle in degrees, describing the field of view
        # stored in the ith element of _obs_field_of_views.
        # If no field-of-view has been specified, it defaults to 360 degrees. The
        # field of view must lie in [0,360]
        #
        # Another optional attribute of each position is the view-direction
        # (x, y, z) stored in the ith element of _obs_view_directions.
        # If no view direction has been specified, it defaults to (1, 0, 0).
        # The view direction must have a magnitude of 1.
        self._obs_positions: List[List[float]] = []
        self._obs_field_of_views: List[float] = []
        self._obs_view_directions: List[Tuple[float, float, float]] = []

        # Solar parameters for each observation point. The solar positions
        # describe the sun position as a 2-tuple (azimuth, altitude).
        # The azimuth is the position on the horizion starting north in clockwise
        # order and expressed in radians where north (+x) is represented by 0, east (+y)
        # by pi/2, south (-x) by pi and west (-y) by 3/2*pi. Intermediate values work
        # as well.
        # The altitude is the height of the sun expressed in radians where
        # the horizion is at 0, the zenith is pi/2.
        # The zenith luminance is expressed in Klux and describes the brightness
        # when looking straight up.
        self._obs_solar_positions: List[List[Tuple[float, float]]] = []
        self._obs_solar_zenith_luminances: List[List[float]] = []

        # Rendering & Computation Settings
        self._sim_resolution = resolution

    def add_triangles(self, triangles, group: str = "default"):
        """Add a triangle to the simulation.

        A triangle is represented by its three vertices a, b and c.
        Each point is three-dimensional and each coordinate is a floating
        point value.

        A triangle can optionally have an assigned group which will later be
        used to compute the visibile area per group for each observation point.

        Args:
            group (str): Defaults to 'default'. The group the triangle belongs to.
        """
        if group not in self._geom_group_to_index:
            self._geom_group_to_index[group] = len(self._geom_groups)
            self._geom_triangles.append(np.ndarray(shape=(0, 3, 3)))
            self._geom_groups.append(group)

        group_index = self._geom_group_to_index[group]
        self._geom_triangles[group_index] = np.vstack(
            [self._geom_triangles[group_index], triangles]
        )

    def add_observation_point(
        self,
        pos: Tuple[float, float, float],
        fov: float = 360.0,
        view_direction: Tuple[float, float, float] = (1, 0, 0),
        solar_pos: List[Tuple[float, float]] = None,
        solar_zenith_luminance: List[float] = None,
    ):
        """Add an observation point to the simulation.

        Args:
            pos (Tuple[float, float, float]): The (x, y, z) position of the
                observation point. Must use the same coordinate system as the
                geometry.
            fov (float): Defaults to 360. The field-of-view describing the
                horizontal and vertical angular width in degrees. The
                field-of-view is a geometrical circular cone with angular
                cone half-width of the specified angle.
            view_direction (Tuple[float, float, float]): Defaults to (1, 0, 0).
                Describes the view direction (thus, the center axis of the field
                of view).
            solar_pos (List[Tuple[float, float]]): Defaults to a single sun position (pi, pi/2).
                Describes (azimuth, altitude) of the sun. The azimuth is the position on the
                horizon in radians from north to east (north=0, east=pi/2,
                south=pi, west=3/2*pi). The altitude is the height of the sun in
                radians (horizon=0, zenith=pi/2).
            solar_zenith_luminance (List[float]): Defaults to 1. The zenith luminance in Klux
        """
        # Normalize paramters
        f = fov % 361
        x, y, z = view_direction
        m = np.linalg.norm(view_direction)
        v = (x / m, y / m, z / m)
        self._obs_positions.append(list(pos))
        self._obs_field_of_views.append(f)
        self._obs_view_directions.append(v)

        if solar_pos is None:
            self._obs_solar_positions.append([(np.pi, np.pi / 2)])
        else:
            self._obs_solar_positions.append(solar_pos)

        if solar_zenith_luminance is None:
            self._obs_solar_zenith_luminances.append([1.0])
        else:
            self._obs_solar_zenith_luminances.append(solar_zenith_luminance)

    def run(
        self,
        run_volume: bool = True,
        run_area: bool = True,
        run_sun: bool = False,
        use_sun_v2: Optional[bool] = False,
    ) -> list:
        """Runs the simulation and return the simulation results.

        Output Format:
        {
            "simulations": {
            "area": float,
            "area_by_group": {
                "group1": float,
                "group2": float,
                ...
            },
            "volume": float
            },
            "field-of-view": float,
            "view-direction": [float, float, float],
            "position": [float, float, float]
            },
            ...
        ]

        Returns:
            list: A list of dictionaries containing the simulations results
                for each observation point. See section "Output Format" above.
        Raises:
            RuntimeError: if error occured
        """

        # Create input data file
        input_data = self.generate_input(
            run_volume, run_area, run_sun, use_sun_v2=use_sun_v2
        )

        # Run simulation
        output_data = ViewWrapper.execute_quavis(quavis_input=input_data)

        return self.parse_quavis_output(output_data=output_data)

    @classmethod
    def execute_quavis(cls, quavis_input: dict) -> dict:
        logger.info("Quavis starting in command line")

        tmp_output_filepath = Path(quavis_input["quavis"]["output"]["filename"])
        tmp_input_filepath = Path(
            tmp_output_filepath.as_posix().replace(
                "".join(tmp_output_filepath.suffixes), ".in.json"
            )
        )
        with tmp_input_filepath.open("w") as output_stream:
            json.dump(quavis_input, output_stream)

        quavis_proc = delegator.run(
            f"{cls._quavis_bin_location.as_posix()} {tmp_input_filepath}", block=True
        )
        logger.info(
            "Quavis command line process finished, reading output and/or errors if any"
        )

        for msg in quavis_proc.out.split("\n"):
            logger.info("Quavis Output: %s", msg)

        if "Done" not in quavis_proc.out and not tmp_output_filepath.exists():
            # HACK: currently we have an issue running quavis in ubuntu 20.04 with an upgraded vulkan version
            # and although the program is generating the output we need it generates a segmentation fault error.
            # quavis_proc.err is always empty, quavis is probably not reporting in the right level
            raise QuavisSimulationException(
                "An error occurred in Quavis: %s. Output: %s"
                % (quavis_proc.err, quavis_proc.out)
            )

        with tmp_output_filepath.open() as input_stream:
            output_data = json.load(input_stream)

        tmp_output_filepath.unlink()
        tmp_input_filepath.unlink()

        return output_data

    def _anti_gpu_glitch_translation(self):
        # In order to avoid GPU glitches when coordinates have high values
        # we translate the coordinates of all geometry and observation points
        # such that the mean observation point position lies at the origin (0, 0, 0).
        self._mean_pos = np.mean(self._obs_positions, axis=0)
        self._obs_positions = (np.array(self._obs_positions) - self._mean_pos).tolist()
        for i, _ in enumerate(self._geom_triangles):
            for j in range(3):
                self._geom_triangles[i][:, :, j] -= self._mean_pos[j]

    def _invert_anti_gpu_glitch_translation(self):
        # inverts _anti_gpu_glitch_translation
        self._obs_positions = (np.array(self._obs_positions) + self._mean_pos).tolist()
        for i, _ in enumerate(self._geom_triangles):
            for j in range(3):
                self._geom_triangles[i][:, :, j] += self._mean_pos[j]

    @classmethod
    def load_wrapper_from_input_no_geometries(cls, input_data: Dict):
        """ "
        Creates a ViewWrapper instance based on the quavis input file. Please note,
        that geometries are not loaded. The method provides all data required for executing
        parse_quavis_output.
        """
        # XXX: Load geometries, too. This is a bit tricky since group assignments
        #      have to be recovered and the data structure of the triangles is
        #      changed in the quavis input generation of the scene objects.
        quavis_input = input_data["quavis"]
        wrapper = ViewWrapper(resolution=quavis_input["rendering"]["renderWidth"])

        # observation points
        wrapper._obs_positions = (
            np.array(quavis_input["observationPoints"]["positions"])
            .reshape(-1, 3)
            .tolist()
        )
        wrapper._obs_view_directions = (
            np.array(quavis_input["observationPoints"]["viewDirections"])
            .reshape(-1, 3)
            .tolist()
        )
        wrapper._obs_field_of_views = quavis_input["observationPoints"]["fieldOfViews"]
        wrapper._obs_solar_zenith_luminances = quavis_input["observationPoints"][
            "solarZenithLuminances"
        ]
        wrapper._obs_solar_positions = list(
            zip(  # type: ignore
                quavis_input["observationPoints"]["solarAzimuths"],
                quavis_input["observationPoints"]["solarAltitudes"],
            )
        )

        # meta data
        wrapper._mean_pos = np.array(quavis_input["metaData"]["_mean_pos"])
        wrapper._geom_groups = quavis_input["metaData"]["_geom_groups"]

        return wrapper

    def parse_quavis_output(self, output_data: dict) -> list:
        """Parse the output of the cpp implementation.

        Args:
            output_data (dict): The dictionary returned as json from the cpp
                process.

        Output Format:
        {
            "simulations": {
            "area": float,
            "area_by_group": {
                "group1": float,
                "group2": float,
                ...
            },
            "volume": float
            },
            "field-of-view": float,
            "view-direction": [float, float, float],
            "position": [float, float, float]
            },
            ...
        ]

        Returns:
            list: A list of dictionaries containing the simulations results
                for each observation point. See section "Output Format" above.
        """
        self._invert_anti_gpu_glitch_translation()

        obs_results = []
        for idx, obs_position in enumerate(self._obs_positions):
            results = output_data["results"][idx]

            # Extract shader stage data
            volume = None
            area = None
            area_by_group = None
            sun = None

            if "volume" in results:
                volume = results["volume"]["values"][0]

            if "groups" in results:
                area = sum(results["groups"]["values"])

                area_by_group = {}
                for group_idx, group in enumerate(self._geom_groups):
                    area_by_group[group] = results["groups"]["values"][group_idx + 1]

            if "sun" in results:
                sun = results["sun"]["values"]

            # generate result dictionary
            obs_result = {
                "position": obs_position,
                "view-direction": self._obs_view_directions[idx],
                "field-of-view": self._obs_field_of_views[idx],
                "simulations": {
                    "volume": volume,
                    "area": area,
                    "area_by_group": area_by_group,
                    "sun": sun,
                },
            }

            obs_results.append(obs_result)

        return obs_results

    def generate_input(
        self,
        run_volume: bool,
        run_area: bool,
        run_sun: bool,
        use_sun_v2: Optional[bool] = False,
        create_images: bool = False,
    ) -> Dict:
        """Generate the input json for the CPP implementation.

        Output Format:
            ```
            {
                'quavis': {
                    'header': dict, // meta data
                    'sceneObjects: dict, // geometry to be rendered
                    'observationPoints: dict, // the observation points
                    'rendering': dict, // rendering settings
                    'computeStages: dict, // compute settings
                    'output': dict // output settings
                }
            }
            ```

        Returns:
            The dictionary representing the CPP json input when serialized
                to json.
        """
        run_id = str(uuid.uuid4())
        output_filepath = self._quavis_io_base_dir.joinpath(run_id).with_suffix(
            ".out.json"
        )

        self._anti_gpu_glitch_translation()

        input_data = {
            "quavis": {
                "header": self._input_header(run_id),
                "sceneObjects": self._input_scene_objects(),
                "observationPoints": self._input_observation_points(),
                "rendering": self._input_rendering(),
                "computeStages": self._input_compute_stages(
                    run_volume=run_volume,
                    run_area=run_area,
                    run_sun=run_sun,
                    create_images=create_images,
                    use_sun_v2=use_sun_v2,
                ),
                "output": self._input_output(output_filepath.as_posix()),
                "metaData": self._input_metadata(),
            }
        }

        return input_data

    def _input_scene_objects(self) -> List[dict]:
        """Generate input json data for the scene objects to be rendered.

        The input is a json describing the geometry, the observation points
        and the shader stages used for the GPU compute pipeline.
        The geometry is, for our purposes, an indexed array of triangles where
        each vertex has an assigned color for group membership affiliation.

        Output Format:
            ```
            [{
                'type': 'indexedArray',
                'positions': list, // vertex positions (x1, y1, z1, ...)
                'vertexData': list, // vertex colors (r1, g1, b1, a1, ...)
                'indices': list, // triangle corners (i1, i2, i3, ...)
                'modelmMatrix': list, // 16 entries (unit matrix)
                'material': {
                    'type': 'vertexData'
                }
            }]
            ```

        Returns:
            List[dict]: The list of scene objects to be rendered.
        """

        # Create a numpy array of shape (k,3,7) containing all triangles
        # with format (x, y, z, red, green, blue, alpha). Each color
        # represents one group and is a non-periodic float value.
        total_num_triangles = sum(
            [group_triangles.shape[0] for group_triangles in self._geom_triangles]
        )
        triangles_array = np.ndarray(shape=(total_num_triangles, 3, 7))
        grp_colors = self._grp_generate_colors(self._MAX_GROUPS)

        current_index = 0
        for idx, triangles in enumerate(self._geom_triangles):
            next_index = current_index + self._geom_triangles[idx].shape[0]
            triangles_array[current_index:next_index, :, :3] = triangles
            triangles_array[current_index:next_index, :, 3:] = grp_colors[idx]
            current_index = next_index

        # Create a set of vertex positions, vertex colors and indices such that
        # each vertex, inluding colors, is unique and a triangle is a 3-tuple
        # of vertex indices.
        triangles_array, indexed_geom_triangles = np.unique(
            triangles_array.reshape(-1, 7), axis=0, return_inverse=True
        )

        # At this point `vertex_positions` is an array of all vertex positions,
        # `vertex_colors` is an array of the corresponding vertex colors and
        # `indexed_geom_triangles` is an array where each row (i1, i2, i3)
        # references a triangle consisting of the points vertex i1, vertex i2
        # and vertex i3.

        # Now convert to the proper input format for the CPP simulation.
        scene_object = {
            "type": "indexedArray",
            "positions": triangles_array[:, :3].flatten().tolist(),
            "vertexData": triangles_array[:, 3:].flatten().tolist(),
            "indices": indexed_geom_triangles.flatten().tolist(),
            "modelMatrix": np.identity(4).flatten().tolist(),
            "material": {"type": "vertexData"},
        }
        return [scene_object]

    @staticmethod
    def _grp_generate_colors(
        number_of_colors: int,
    ) -> List[Tuple[int, float, float, float]]:
        """Generate a list of n unique rgba colors.

        Returns A list of (r, g, b, a) tuples representing the associated colors for 0..n-1

        Todo:
            We could use an n-ary Gray Code instead to make an on-line color
            generation with a predefined maximum number of colors.
        """
        return [(key, 0.0, 0.0, 1.0) for key in range(1, number_of_colors + 1)]

    def _input_observation_points(self) -> Dict:
        """[summary]

        Returns:
            dict: [description]
        """

        positions = np.array(self._obs_positions).flatten().tolist()
        field_of_views = np.array(self._obs_field_of_views).flatten().tolist()
        view_directions = np.array(self._obs_view_directions).flatten().tolist()
        solar_azimuths = [
            np.array(x)[:, 0].flatten().tolist() for x in self._obs_solar_positions
        ]
        solar_altitudes = [
            np.array(x)[:, 1].flatten().tolist() for x in self._obs_solar_positions
        ]
        solar_zenith_luminances = self._obs_solar_zenith_luminances

        observation_points = {
            "positions": positions,
            "fieldOfViews": field_of_views,
            "viewDirections": view_directions,
            "solarAzimuths": solar_azimuths,
            "solarAltitudes": solar_altitudes,
            "solarZenithLuminances": solar_zenith_luminances,
        }

        return observation_points

    def _input_rendering(self) -> Dict:
        """Generate the rendering section of the input data of the simulation.

        Output Format:
            ```
            {
                'renderWidth': int,
                'renderHeight': int
            }
            ```

        Returns:
            dict: The rendering section
        """
        render_width = self._sim_resolution
        render_height = self._sim_resolution

        rendering = {"renderWidth": render_width, "renderHeight": render_height}

        return rendering

    def _input_compute_stages(
        self,
        run_volume: bool,
        run_area: bool,
        run_sun: bool,
        create_images: bool = False,
        use_sun_v2: Optional[bool] = False,
    ) -> List[Dict[str, Any]]:
        """Generate the compute stages section of the simulation input.

        Each compute stage can be regarded as a simulation type being performed
        on the rendered image. E.g. `volume` computes the visible volume and
        `area` computes the spherical area.

        Output Format:
            ```
            [
                {
                    'type': str,
                    'name': str
                },
                ...
            ]
            ```

        Args:
            create_images (bool): Create rendering images for each point?

        Returns:
            dict: The compute stage section
        """
        volume_stage = {"type": "volume", "name": "volume"}
        group_stage = {
            "type": "groups",
            "name": "groups",
            "max_groups": self._MAX_GROUPS,
        }

        solar_stage = {"type": "sun", "name": "sun"}
        if use_sun_v2:
            solar_stage["type"] = "sunv2"

        stages: List[Dict[str, Any]] = []
        if run_volume:
            stages.append(volume_stage)
        if run_area:
            stages.append(group_stage)
        if run_sun:
            stages.append(solar_stage)

        if create_images:
            image_stage = {"type": "cubeMap", "name": "image", "pretty": True}
            stages.append(image_stage)

        return stages

    def _input_header(self, run_name: str) -> Dict:
        """Generate the header section of the input data of the simulation.

        Output Format:
            ```
            {
                'name': str // the name of the simulation run
            }
            ```

        Args:
            run_name (str): The name of this simulation run.

        Returns:
            dict: The header section of the CPP input as dictionary to be
                serialized to json.
        """
        header = {"name": run_name}

        return header

    def _input_output(
        self,
        filename: str,
        image_format: str = "png",
        image_names: str = "{0:0>4}_{1}.png",
    ) -> Dict:
        """Generate the output section of the input data of the simulation.

        Output Format:
            ```
            {
                'filename': str // the filename where to store the data
            }
            ```

        Args:
            filename (str): The path to the output file.
            image_format (str): image format
            image_names (str): image name

        Returns:
            dict: The output section of the CPP input as dictionary to be
                serialized to json.
        """
        # TODO: Add parameter for image naming
        output = {
            "filename": filename,
            "imagesType": image_format,
            "imageNaming": image_names,
        }

        return output

    def _input_metadata(self) -> Dict:
        """
        Provides metadata required for the reconstruction of the wrapper
        from the input file (see `ViewWrapper.load_wrapper_from_input_no_geometries`)
        """
        return {"_mean_pos": self._mean_pos.tolist(), "_geom_groups": self._geom_groups}
