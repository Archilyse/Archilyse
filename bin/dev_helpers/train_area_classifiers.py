from pathlib import Path

from brooks.area_classifier import AreaClassifier
from brooks.classifications import CLASSIFICATIONS
from brooks.types import AreaType
from common_utils.exceptions import (
    InaccurateClassifierException,
    NotEnoughTrainingDataClassifierException,
)
from common_utils.logger import logger

CLASSIFIER_FOLDER = Path("/usr/classifiers/")
CLASSIFIER_FOLDER.mkdir(parents=True, exist_ok=True)
for classification_scheme in CLASSIFICATIONS:
    classifier = AreaClassifier(classification_scheme)
    try:
        classifier.train(
            output_path=CLASSIFIER_FOLDER.joinpath(f"{classification_scheme}.pickle"),
            n_jobs=8,
            tune_model=False,
            min_model_accuracy=0.8,
            ignore_area_types={AreaType.KITCHEN_DINING.name},
        )
    except NotEnoughTrainingDataClassifierException:
        logger.info(
            f"Skipping {classification_scheme} due to insufficient training data"
        )
    except InaccurateClassifierException:
        logger.info(f"Skipping {classification_scheme} due to inaccurate classifier")
