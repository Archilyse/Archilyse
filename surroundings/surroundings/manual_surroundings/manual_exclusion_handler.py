from common_utils.constants import ManualSurroundingTypes
from surroundings.manual_surroundings.utils import FeatureProviderMixin


class ManualExclusionSurroundingHandler(FeatureProviderMixin):
    manual_surrounding_type = ManualSurroundingTypes.EXCLUSION_AREA
