import random
from dataclasses import dataclass
from itertools import chain, groupby
from math import ceil
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd
from joblib import Parallel, delayed
from shapely.affinity import scale
from shapely.geometry import Point
from tqdm import tqdm

from brooks.models import SimLayout
from common_utils.logger import logger
from handlers import PlanHandler, PlanLayoutHandler
from handlers.db import PlanDBHandler


@dataclass
class ImageMetadata:
    image_hash: str
    filename: str
    mime_type: str
    width: int
    height: int
    plan_id: int


@dataclass
class PlanAnnotationElement:
    image_hash: str
    supertype: str
    type: str
    wkt_footprint_exact: str
    wkt_fotprint_oriented_bounding_box: str
    wkt_centroid: str


def save_plan_image(plan_handler: PlanHandler, image_path: Path):
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_content = plan_handler.get_plan_image_as_bytes()
    with image_path.open("wb") as f:
        f.write(image_content)


def transform_layout_to_match_plan_image(layout: SimLayout, plan_id: int):
    from handlers.editor_v2 import ReactPlannerHandler
    from simulations.view.meshes import GeoreferencingTransformation

    georef = GeoreferencingTransformation()

    georef.set_translation(
        x=0,
        y=-ReactPlannerHandler().image_height(plan_id=plan_id),
        z=0,
    )
    layout.apply_georef_transformation(georeferencing_transformation=georef)
    return layout


def save_annotation_data(plan_handler: PlanLayoutHandler, annotation_path: Path):
    layout = plan_handler.get_layout(classified=True)
    layout = transform_layout_to_match_plan_image(
        layout=layout, plan_id=plan_handler.plan_id
    )
    image_annotations = [
        PlanAnnotationElement(
            image_hash=plan_handler.plan_info["image_hash"],
            supertype=element.type.__class__.__name__,
            type=element.type.name,
            wkt_footprint_exact=scale(
                geom=element.footprint, yfact=-1, origin=Point(0, 0)
            ).wkt,
            wkt_fotprint_oriented_bounding_box=scale(
                geom=element.footprint.minimum_rotated_rectangle,
                yfact=-1,
                origin=Point(0, 0),
            ).wkt,
            wkt_centroid=scale(
                geom=element.footprint.centroid, yfact=-1, origin=Point(0, 0)
            ).wkt,
        )
        for element in layout.separators
        | layout.openings
        | layout.features
        | layout.areas
        if element.footprint.area > 1
    ]

    if not image_annotations:
        raise ValueError("Not enough annotation data.")

    annotation_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(image_annotations).to_csv(annotation_path, index=False)


def save_image_and_get_annotation(plan_id: int, image_dir: Path, annotation_dir: Path):
    plan_handler = PlanLayoutHandler(plan_id=plan_id)

    image_filename = f"{plan_handler.plan_info['image_hash']}.{plan_handler.plan_info['image_mime_type'].split('/')[-1]}"
    image_path = image_dir.joinpath(image_filename)
    annotation_path = annotation_dir.joinpath(
        f"{plan_handler.plan_info['image_hash']}.csv"
    )

    try:
        if not annotation_path.is_file():
            save_annotation_data(
                plan_handler=plan_handler,
                annotation_path=annotation_path,
            )
        if not image_path.is_file():
            save_plan_image(
                plan_handler=PlanHandler(plan_id=plan_id), image_path=image_path
            )
    except Exception as e:
        logger.warning(f"Error saving plan {plan_id}: {str(e)}")

        if annotation_path.is_file():
            annotation_path.unlink()

        if image_path.is_file():
            image_path.unlink()

        return

    return ImageMetadata(
        image_hash=plan_handler.plan_info["image_hash"],
        mime_type=plan_handler.plan_info["image_mime_type"],
        width=plan_handler.plan_info["image_width"],
        height=plan_handler.plan_info["image_height"],
        filename=image_filename,
        plan_id=plan_id,
    )


def save_dataset(plan_ids: Iterable[int], base_dir: Path, n_jobs=16):
    logger.info(f"Saving {len(train_plan_ids)} samples to {base_dir.as_posix()}")

    dataset = [
        metadata
        for metadata in Parallel(n_jobs=n_jobs, backend="multiprocessing")(
            delayed(save_image_and_get_annotation)(
                plan_id=plan_id,
                image_dir=base_dir.joinpath("images/"),
                annotation_dir=base_dir.joinpath("../annotations/"),
            )
            for plan_id in tqdm(plan_ids)
        )
        if metadata
    ]
    pd.DataFrame(dataset).to_csv(base_dir.joinpath("images.csv"), index=False)


def get_train_test_plan_ids(ratio_test_sites: float) -> Tuple[Tuple[int], Tuple[int]]:
    plan_ids_by_site_id = {
        site_id: {plan_info["id"] for plan_info in plan_infos}
        for site_id, plan_infos in groupby(
            sorted(
                PlanDBHandler.find(
                    annotation_finished=True, output_columns=["id", "site_id"]
                ),
                key=lambda z: z["site_id"],
            ),
            key=lambda z: z["site_id"],
        )
    }

    site_ids = sorted(plan_ids_by_site_id.keys())
    num_test_sites = ceil(len(site_ids) * ratio_test_sites)

    random.seed(42)
    random.shuffle(site_ids)
    test_plan_ids = chain(
        *[plan_ids_by_site_id[site_id] for site_id in site_ids[:num_test_sites]]
    )
    train_plan_ids = chain(
        *[plan_ids_by_site_id[site_id] for site_id in site_ids[num_test_sites:]]
    )

    return tuple(train_plan_ids), tuple(test_plan_ids)


if __name__ == "__main__":
    output_path = Path("/home/mfranzen/Downloads/omdena/")
    train_plan_ids, test_plan_ids = get_train_test_plan_ids(ratio_test_sites=0.05)
    save_dataset(plan_ids=train_plan_ids, base_dir=output_path.joinpath("train/"))
    save_dataset(plan_ids=test_plan_ids, base_dir=output_path.joinpath("test/"))
