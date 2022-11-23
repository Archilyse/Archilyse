import pickle
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pkg_resources
from joblib import Parallel, delayed
from sklearn.metrics import accuracy_score, make_scorer
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils import resample
from tqdm import tqdm
from xgboost.sklearn import XGBClassifier

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimLayout
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.exceptions import (
    AreaMismatchException,
    InaccurateClassifierException,
    InvalidShapeException,
    NoClassifierAvailableException,
    NotEnoughTrainingDataClassifierException,
)
from common_utils.logger import logger
from handlers import PlanHandler, PlanLayoutHandler
from handlers.db import PlanDBHandler, SiteDBHandler
from simulations.room_shapes import get_room_shapes


class AreaClassifier:
    @staticmethod
    def deprecated_features() -> Set[str]:
        return {"URINAL"}

    @staticmethod
    def untrained_features() -> Set[str]:
        return {"OFFICE_DESK"}

    @classmethod
    def ALLOWED_FEATURES(cls) -> Set[str]:
        return (
            {feature.name for feature in FeatureType}
            - cls.deprecated_features()
            - cls.untrained_features()
        )

    def ALLOWED_AREA_TYPES(self) -> Set[str]:
        return {
            area_type.name for area_type in self._classification_scheme.area_types
        } - {AreaType.NOT_DEFINED.name}

    def __init__(self):
        self._classification_scheme = UnifiedClassificationScheme()
        self._label_encoder = LabelEncoder()
        self._label_encoder.fit(
            sorted([area_type for area_type in self.ALLOWED_AREA_TYPES()])
        )

    def load(self):
        classification_scheme_path = CLASSIFIER_DIR.joinpath(
            "CLASSIFICATIONS.UNIFIED.pickle"
        )
        try:
            with classification_scheme_path.open("rb") as fh:
                self._classifier = pickle.load(fh)
        except FileNotFoundError:
            raise NoClassifierAvailableException(
                f"No classifier found for classification scheme {self._classification_scheme}"
                f" at {classification_scheme_path}"
            )

    # Classification

    def classify(self, plan_layout: SimLayout, area: SimArea) -> AreaType:
        return self._decode_labels(
            self._classifier.predict(
                [self._compute_feature_vector(plan_layout=plan_layout, area=area)]
            )
        )[0]

    def _encode_labels(self, area_types: List[AreaType]) -> List[int]:
        return self._label_encoder.transform(
            [area_type.name for area_type in area_types]
        )

    def _decode_labels(self, labels: List[int]) -> List[AreaType]:
        return [
            AreaType[class_name]
            for class_name in self._label_encoder.inverse_transform(labels)
        ]

    @classmethod
    def _compute_feature_vector(
        cls, plan_layout: SimLayout, area: SimArea
    ) -> List[int]:
        feature_type_counter = Counter([feature.type.name for feature in area.features])
        opening_type_counter = Counter(
            [opening.type for opening in plan_layout.areas_openings[area.id]]
        )
        separator_type_counter = Counter(
            [separator.type for separator in plan_layout.areas_separators[area.id]]
        )
        return (
            [
                area.footprint.area,
                area.footprint.length,
                *get_room_shapes(area.footprint).values(),
            ]
            + [
                feature_type_counter[feature_type]
                for feature_type in sorted(cls.ALLOWED_FEATURES())
            ]
            + [
                opening_type_counter[opening_type]
                for opening_type in sorted(OpeningType, key=lambda z: z.name)
            ]
            + [
                separator_type_counter[separator_type]
                for separator_type in sorted(SeparatorType, key=lambda z: z.name)
            ]
        )

    # Training

    def train(
        self,
        output_path: Path,
        dataset_size: Optional[int] = None,
        ignore_area_types: Optional[Set[str]] = None,
        min_required_plans: int = 10,
        min_model_accuracy: float = 0.9,
        n_jobs: int = 1,
        tune_model: bool = False,
    ):
        if not ignore_area_types:
            ignore_area_types = set()

        logger.info(f"Loading training data for {self._classification_scheme}")
        plan_layouts = self._load_training_data(
            dataset_size=dataset_size,
            min_required_plans=min_required_plans,
            n_jobs=n_jobs,
        )

        logger.info("Computing features...")
        feature_vectors, area_types = zip(
            *[
                (
                    self._compute_feature_vector(plan_layout=plan_layout, area=area),
                    area.type,
                )
                for plan_layout in plan_layouts
                for space in plan_layout.spaces
                for area in space.areas
                if area.type in self._classification_scheme.area_types
                and area.type.name in (self.ALLOWED_AREA_TYPES() - ignore_area_types)
            ]
        )
        labels: Iterable[int] = self._encode_labels(area_types=area_types)

        logger.info("Tuning model...")
        clf_model = Pipeline(
            [("scaler", StandardScaler()), ("classifier", XGBClassifier())]
        )
        clf_parameters = {
            "classifier__min_child_weight": [0.8, 1, 1.2],
            "classifier__gamma": [0, 0.1, 0.2],
            "classifier__max_depth": [4, 6, 8],
            "classifier__subsample": [1.0],
            "classifier__colsample_bytree": [1.0],
        }

        clf = self._optimize_and_validate_model(
            model=clf_model,
            grid_search_parameters=clf_parameters if tune_model else {},
            data_input=feature_vectors,
            expected_output=labels,
            min_model_accuracy=min_model_accuracy,
            n_jobs=n_jobs,
        )

        logger.info("Training model...")
        clf.fit(X=feature_vectors, y=labels)
        with output_path.open("wb") as fh:
            pickle.dump(clf, fh)

    def _optimize_and_validate_model(
        self,
        model: Pipeline,
        grid_search_parameters: Dict,
        data_input: List[Tuple],
        expected_output: Iterable[int],
        min_model_accuracy: float,
        n_jobs: int,
        grid_search_score=accuracy_score,
    ):
        # 1st we do a hyper-parameter tuning on 40% of the data
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=grid_search_parameters,
            cv=5,
            scoring=make_scorer(grid_search_score),
            n_jobs=n_jobs,
            verbose=1,
        )
        grid_search.fit(
            *resample(data_input, expected_output, n_samples=int(len(data_input) * 0.4))
        )

        logger.info(
            f"Hyper-parameter tuning of {self._classification_scheme} "
            f"yielded best score {grid_search.best_score_} "
            f"with params {grid_search.best_params_} "
        )

        # 2nd we validate the best estimator on all data
        # via cross validation
        cv_scores = cross_val_score(
            grid_search.best_estimator_,
            data_input,
            expected_output,
            cv=5,
            scoring=make_scorer(accuracy_score),
        )
        if cv_scores.mean() < min_model_accuracy:
            raise InaccurateClassifierException(
                f"Model of {self._classification_scheme} did "
                f"not reach {min_model_accuracy*100}% accuracy: {cv_scores.mean()})"
            )

        logger.info(
            f"Validated model for {self._classification_scheme} "
            f"with scores {cv_scores} "
            f"and mean score {cv_scores.mean()}"
        )

        return grid_search.best_estimator_

    def _load_training_data(
        self,
        min_required_plans: int,
        n_jobs: int,
        dataset_size: Optional[int] = None,
    ):
        site_ids = [
            site["id"]
            for site in SiteDBHandler.find(
                full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
                output_columns=["id"],
            )
        ]

        plan_ids = [
            plan["id"]
            for plan in PlanDBHandler.find_in(
                site_id=site_ids,
                output_columns=[
                    "id",
                    "annotation_finished",
                    "georef_scale",
                    "georef_x",
                    "georef_y",
                    "georef_rot_x",
                    "georef_rot_y",
                    "georef_rot_angle",
                ],
            )
            if plan["annotation_finished"]
            and PlanHandler(plan_info=plan).is_georeferenced
        ]

        if len(plan_ids) < min_required_plans:
            raise NotEnoughTrainingDataClassifierException(
                f"Training for classification scheme {self._classification_scheme}"
                f"failed, minimum number {min_required_plans} not reached."
            )

        if dataset_size:
            plan_ids = plan_ids[:dataset_size]

        return [
            plan_layout
            for plan_layout in Parallel(n_jobs=n_jobs)(
                delayed(self._load_plan)(plan_id) for plan_id in tqdm(plan_ids)
            )
            if plan_layout
        ]

    @staticmethod
    def _load_plan(plan_id):
        try:
            return PlanLayoutHandler(plan_id=plan_id).get_layout(
                scaled=True, classified=True
            )
        except InvalidShapeException:
            pass
        except AreaMismatchException:
            pass


CLASSIFIER_DIR = Path(pkg_resources.resource_filename("brooks", "data/classifiers/"))
