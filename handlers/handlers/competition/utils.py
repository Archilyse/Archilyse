import copy
from typing import Dict, List, Union

from common_utils.competition_constants import (
    ARCHILYSE_FEATURES,
    CATEGORIES,
    RED_FLAGS_FEATURES,
    UPLOADED_FEATURES,
    CompetitionFeatures,
)


def f_to_str(val: Union[float, str]) -> str:
    return f"{float(val):.1f}"


class CompetitionCategoryTreeGenerator:
    def __init__(
        self,
        red_flags_enabled: bool,
        features_selected: List[CompetitionFeatures] = None,
    ):
        self.red_flags_enabled = red_flags_enabled
        self.features_selected = features_selected

    def get_category_tree(self) -> List[Dict]:

        category_tree = []
        for category in CATEGORIES:
            # Copy all info but sub_sections (children)
            category_tree.append(
                copy.deepcopy(
                    {k: v for k, v in category.items() if k != "sub_sections"}
                )
            )
            category_tree[-1]["sub_sections"] = self._generate_sub_category(
                category["sub_sections"]
            )

        return category_tree

    def _generate_sub_category(self, sub_sections) -> List[Dict]:
        features_filter = [
            f.value for f in self.features_selected or list(CompetitionFeatures)
        ]
        filtered_sub_sections = []
        for sub_section in sub_sections:
            leaves_to_keep = []
            for leaf_level in sub_section["sub_sections"]:
                if leaf_level["key"] in features_filter:
                    copied_leaf = copy.deepcopy(leaf_level)
                    self._category_leaf_enrich(copied_leaf)
                    leaves_to_keep.append(copied_leaf)

            if leaves_to_keep:
                # Copy all subsection data but the leaves
                filtered_sub_sections.append(
                    copy.deepcopy(
                        {k: v for k, v in sub_section.items() if k != "sub_sections"}
                    )
                )
                #  Adds the selected leaves
                filtered_sub_sections[-1]["sub_sections"] = leaves_to_keep
        return filtered_sub_sections

    def _category_leaf_enrich(self, leaf_level: Dict):
        if leaf_level["key"] in ARCHILYSE_FEATURES:
            leaf_level["archilyse"] = True
        if leaf_level["key"] in UPLOADED_FEATURES:
            leaf_level["uploaded"] = True
        if self.red_flags_enabled and leaf_level["key"] in RED_FLAGS_FEATURES:
            leaf_level["red_flag"] = True
