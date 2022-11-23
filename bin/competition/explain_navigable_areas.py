from typing import Optional

from matplotlib import pyplot

from brooks import SpaceConnector
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_polygons
from handlers import PlanHandler
from handlers.competition import CompetitionFeaturesCalculator


def get_site_plans(
    site_id: int,
    building_id: Optional[int] = None,
    floor_number: Optional[int] = None,
):
    site_plans = [
        site_plan
        for site_plan in PlanHandler.get_site_plans_layouts_with_building_floor_numbers(
            site_id=site_id
        )
        if not any(fn < 0 for fn in site_plan["floor_numbers"])
        and not (building_id is not None and building_id != site_plan["building_id"])
        and not (
            floor_number is not None and floor_number not in site_plan["floor_numbers"]
        )
    ]
    site_plans = sorted(
        site_plans, key=lambda p: (p["building_id"], min(p["floor_numbers"]))
    )
    return site_plans


def get_spaces_and_openings(plan_layout):
    return [
        (
            space,
            [
                opening.footprint
                for opening in plan_layout.spaces_openings[space.id]
                if opening.type in {OpeningType.DOOR, OpeningType.ENTRANCE_DOOR}
                and SpaceConnector.get_perpendicular_line_to_largest_side_of_polygon(
                    opening.footprint
                ).intersects(space.footprint)
            ],
        )
        for space in plan_layout.spaces
        if not any(area.type == AreaType.SHAFT for area in space.areas)
    ]


def draw_navigable_space(space, corridor_width, color):
    navigable_space = CompetitionFeaturesCalculator._get_navigable_space(
        space.footprint, corridor_width
    )
    for p in get_polygons(navigable_space):
        pyplot.plot(*p.exterior.xy, color=color, zorder=1)
        for h in p.interiors:
            pyplot.plot(*h.xy, color=color, zorder=1)


def draw_separators(spaces_separators):
    for s in spaces_separators:
        if s.type in (SeparatorType.WALL, SeparatorType.COLUMN):
            pyplot.fill(*s.footprint.exterior.xy, color="black", zorder=2)
        elif s.type == SeparatorType.RAILING:
            pyplot.fill(*s.footprint.exterior.xy, color="white", zorder=3)
            pyplot.plot(*s.footprint.exterior.xy, color="black", zorder=4)


def draw_openings(openings):
    for o in openings:
        pyplot.fill(*o.exterior.xy, color="white", zorder=5)
        pyplot.plot(*o.exterior.xy, color="black", zorder=6)


def get_title(site_plan):
    return f"Building_ID_{site_plan['building_id']}_Floors_{'_'.join({str(f) for f in sorted(site_plan['floor_numbers'])})}"


def explain_navigable_areas(
    site_id: int,
    building_id: Optional[int] = None,
    floor_number: Optional[int] = None,
    failed_only: bool = True,
    by_space: bool = False,
    corridor_width: float = 1.2,
):
    for site_plan in get_site_plans(
        site_id=site_id, building_id=building_id, floor_number=floor_number
    ):
        plan_layout = site_plan["plan_layout"]
        for space, openings in get_spaces_and_openings(plan_layout):
            is_navigable = CompetitionFeaturesCalculator.is_navigable(
                space_footprint=space.footprint,
                opening_footprints=openings,
                corridor_width=corridor_width,
            )
            if failed_only and is_navigable:
                continue

            color = "green" if is_navigable else "red"

            draw_navigable_space(space, corridor_width, color)
            draw_separators(plan_layout.spaces_separators[space.id])
            draw_openings(openings)

            text_location = space.footprint.representative_point()
            pyplot.text(
                x=text_location.x,
                y=text_location.y,
                s=" ".join({a.type.name for a in space.areas}),
                ha="center",
                va="center",
                color=color,
                weight="bold" if not is_navigable else None,
                zorder=10,
            )

            if by_space:
                pyplot.title(get_title(site_plan))
                pyplot.show()

        if not by_space:
            pyplot.title(get_title(site_plan))
            pyplot.show()


explain_navigable_areas(site_id=3089, failed_only=False)
