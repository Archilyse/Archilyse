from common_utils.competition_constants import CATEGORIES, CompetitionFeatures
from handlers.competition.utils import CompetitionCategoryTreeGenerator


def test_competition_get_category_tree_no_feature_selected():
    cat_tree = CompetitionCategoryTreeGenerator(
        red_flags_enabled=False
    ).get_category_tree()
    for cat_1, cat_2 in zip(cat_tree, CATEGORIES):
        assert cat_1["key"] == cat_2["key"]
        for sub_section_1, sub_section_2 in zip(
            cat_1["sub_sections"], cat_2["sub_sections"]
        ):
            assert sub_section_1["key"] == sub_section_2["key"]
            for leaf_level_1, leaf_level_2 in zip(
                sub_section_1["sub_sections"], sub_section_2["sub_sections"]
            ):
                assert leaf_level_1["key"] == leaf_level_2["key"]


def test_competition_get_category_tree_all_but_one_feature_selected():
    removed_feature = CompetitionFeatures.NOISE_STRUCTURAL
    cat_tree = CompetitionCategoryTreeGenerator(
        red_flags_enabled=False,
        features_selected=[f for f in CompetitionFeatures if f != removed_feature],
    ).get_category_tree()
    for cat_1, cat_2 in zip(cat_tree, CATEGORIES):
        assert cat_1["key"] == cat_2["key"]
        for sub_section_1, sub_section_2 in zip(
            cat_1["sub_sections"], cat_2["sub_sections"]
        ):
            assert sub_section_1["key"] == sub_section_2["key"]
            if sub_section_1["key"] == "noise":
                # This one have one less member
                generated_members = {f["key"] for f in sub_section_1["sub_sections"]}
                full_members = {f["key"] for f in sub_section_2["sub_sections"]}
                assert len(generated_members) == len(full_members) - 1
                assert removed_feature.value not in generated_members
                assert removed_feature.value in full_members
            else:
                for leaf_level_1, leaf_level_2 in zip(
                    sub_section_1["sub_sections"], sub_section_2["sub_sections"]
                ):
                    assert leaf_level_1["key"] == leaf_level_2["key"]


def test_competition_get_category_tree_feature_selected_section_empty():
    """ "tests that if we remove all leaf members, then the subsection is removed"""
    removed_features = {
        CompetitionFeatures.NOISE_STRUCTURAL,
        CompetitionFeatures.NOISE_INSULATED_ROOMS,
    }
    removed_subsection = "noise"
    cat_tree = CompetitionCategoryTreeGenerator(
        red_flags_enabled=False,
        features_selected=[f for f in CompetitionFeatures if f not in removed_features],
    ).get_category_tree()
    for cat_1, cat_2 in zip(cat_tree, CATEGORIES):
        assert cat_1["key"] == cat_2["key"]
        if cat_1["key"] == "architecture_usage":
            #  This one have one subsection less, Noise
            generated_members = {f["key"] for f in cat_1["sub_sections"]}
            full_members = {f["key"] for f in cat_2["sub_sections"]}
            assert len(generated_members) == len(full_members) - 1
            assert removed_subsection not in generated_members
            assert removed_subsection in full_members
        else:
            for sub_section_1, sub_section_2 in zip(
                cat_1["sub_sections"], cat_2["sub_sections"]
            ):
                assert sub_section_1["key"] == sub_section_2["key"]
                for leaf_level_1, leaf_level_2 in zip(
                    sub_section_1["sub_sections"], sub_section_2["sub_sections"]
                ):
                    assert leaf_level_1["key"] == leaf_level_2["key"]
