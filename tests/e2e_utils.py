import os


class SlamUIClient:
    @classmethod
    def _base_url(cls):
        return f"http://{os.environ['SLAM_API_INTERNAL_URL']}"

    @classmethod
    def _base_login_url(cls):
        return f"{cls._base_url()}/login"

    @classmethod
    def _base_editor_url(cls):
        return f"{cls._base_url()}/editor/"

    @classmethod
    def _base_editor_v2_url(cls):
        return f"{cls._base_url()}/v2/editor"

    @classmethod
    def _base_potential_view_v2_url(cls):
        return f"{cls._base_url()}/v2/viewer"

    @classmethod
    def _base_classification_url(cls):
        return f"{cls._base_url()}/classification"

    @classmethod
    def _base_linking_url(cls):
        return f"{cls._base_url()}/linking"

    @classmethod
    def _base_georeference_url(cls):
        return f"{cls._base_url()}/georeference"

    @classmethod
    def _base_splitting_url(cls):
        return f"{cls._base_url()}/splitting"

    @classmethod
    def _base_scaling_url(cls):
        return f"{cls._base_url()}/scaling"

    @classmethod
    def quality_url(cls, site_id: int):
        return f"{cls._base_url()}/quality/{site_id}"

    @classmethod
    def heatmaps_url(cls, site_id: int):
        return f"{cls._base_url()}/heatmaps/{site_id}"

    @classmethod
    def _georeference_url_plan(cls, plan_id: int):
        return f"{cls._base_georeference_url()}/{plan_id}"

    @classmethod
    def _linking_url_plan(cls, plan_id: int):
        return f"{cls._base_linking_url()}/{plan_id}"

    @classmethod
    def _classification_url_plan(cls, plan_id: int):
        return f"{cls._base_classification_url()}/{plan_id}"

    @classmethod
    def _splitting_url_plan(cls, plan_id: int):
        return f"{cls._base_splitting_url()}/{plan_id}"

    @classmethod
    def _scaling_url_plan(cls, plan_id: int):
        return f"{cls._base_scaling_url()}/{plan_id}"
