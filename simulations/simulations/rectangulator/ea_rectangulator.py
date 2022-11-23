import math
import random
from typing import Callable, List, Tuple

from deap import algorithms, base, creator, tools
from shapely import wkt
from shapely.geometry import Polygon

from common_utils.exceptions import RectangleNotCalculatedException
from simulations.rectangulator.rectangle_dims_handler import (
    PolDims,
    RectangleDimsHandler,
)

POPULATION_SIZE = 200
PREGENERATED_POPULATION_SPLIT = 0.9


def evaluate(target_convex_polygon: Polygon, raw: Tuple) -> List[float]:
    """Return type is imposed by the deap framework although we are looking only for the one value in the list"""
    new_polygon = RectangleDimsHandler.dims_to_polygon(dims=PolDims(*raw))

    if not new_polygon.is_valid:
        return [0.0]
    elif new_polygon.within(target_convex_polygon):
        return [new_polygon.area]
    return [0.0]


def get_max_rectangle_in_convex_polygon(
    target_convex_polygon: Polygon, generations: int = 10
) -> Polygon:
    """Simple maximize function of the area of the maximum rectangle that can be fitted into a convex polygon.
    We use the AnnotationItem data model, so the individual have x, y, width, height and angle attributes that
    are evolving until finding the best combination that maximizes the areas."""

    # If polygon is already a rectangle, return the polygon itself
    if math.isclose(
        target_convex_polygon.minimum_rotated_rectangle.area, target_convex_polygon.area
    ):
        return target_convex_polygon.minimum_rotated_rectangle

    # Fitness function to maximize
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    min_width_height = 0.01
    max_width = target_convex_polygon.bounds[2] - target_convex_polygon.bounds[0]
    max_height = target_convex_polygon.bounds[3] - target_convex_polygon.bounds[1]

    # Definition of the problem
    toolbox = base.Toolbox()
    # How do we evaluate the performance of each individual
    toolbox.register("evaluate", evaluate, target_convex_polygon)

    # Structured custom initializers for each dimension of the new individuals or rectangles
    toolbox.register(
        "attr_x",
        random.uniform,
        target_convex_polygon.bounds[0],
        target_convex_polygon.bounds[2],
    )
    toolbox.register(
        "attr_y",
        random.uniform,
        target_convex_polygon.bounds[1],
        target_convex_polygon.bounds[3],
    )
    toolbox.register(
        "attr_width",
        random.uniform,
        min_width_height,
        max_width,
    )
    toolbox.register("attr_height", random.uniform, min_width_height, max_height)
    toolbox.register("attr_angle", random.uniform, 0, 180)

    toolbox.register(
        "individual",
        tools.initCycle,
        creator.Individual,
        (
            toolbox.attr_x,
            toolbox.attr_y,
            toolbox.attr_width,
            toolbox.attr_height,
            toolbox.attr_angle,
        ),
        n=1,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=2, indpb=0.2)
    toolbox.register("select", tools.selTournament, tournsize=3)

    toolbox.register(
        "population_guess",
        initPopulation,
        creator.Individual,
        POPULATION_SIZE,
        target_convex_polygon,
    )

    initial_population = toolbox.population_guess(toolbox.population)
    # best performing individual
    hof = tools.HallOfFame(1)

    algorithms.eaSimple(
        initial_population,
        toolbox,
        cxpb=0.8,
        mutpb=0.8,
        ngen=generations,
        halloffame=hof,
        verbose=False,
        stats=None,
    )

    # The hof holds only the raw data input sent to the fitness function
    result = evaluate(target_convex_polygon=target_convex_polygon, raw=hof[0])
    if result[0] == 0.0:
        raise RectangleNotCalculatedException(
            f"Couldn't find an optimal rectangle to fit in the target polygon {wkt.dumps(target_convex_polygon)}"
        )
    return RectangleDimsHandler.dims_to_polygon(dims=PolDims(*hof[0]))


def initPopulation(
    ind_init,
    population_size: int,
    target_convex_polygon: Polygon,
    new_individuals_generator: Callable,
):
    from simulations.rectangulator import DeterministicRectangulator

    # Init population with the deterministic rectangulator
    possible_solutions = DeterministicRectangulator(
        polygon=target_convex_polygon,
        resolution=200,
        distance_from_wall=0.01,
    ).get_possible_solutions()

    population = [
        ind_init(x for x in RectangleDimsHandler.polygon_to_dims(pol))
        for pol in sorted(possible_solutions, key=lambda p: p.area)
    ][: round(population_size * PREGENERATED_POPULATION_SPLIT)]

    # Add some random individuals
    for _ in range(10):
        new_individuals = new_individuals_generator(n=population_size)
        valid_individuals = [
            x
            for x in new_individuals
            if evaluate(target_convex_polygon=target_convex_polygon, raw=x) != [0.0]
        ]
        population.extend(valid_individuals[: population_size - len(population)])
        if len(population) >= population_size:
            return population
    return population
