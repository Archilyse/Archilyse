import os
from distutils.util import strtobool

from common_utils.constants import (
    GOOGLE_CLOUD_DXF_FILES,
    GOOGLE_CLOUD_RESULT_IMAGES,
    GOOGLE_CLOUD_SITE_IFC_FILES,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
)

GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE = {
    SUPPORTED_OUTPUT_FILES.PNG: {
        language: f"gcs_{language.name.lower()}_floorplan_link"
        for language in SUPPORTED_LANGUAGES
    },
    SUPPORTED_OUTPUT_FILES.PDF: {
        language: f"gcs_{language.name.lower()}_pdf_link"
        for language in SUPPORTED_LANGUAGES
    },
    SUPPORTED_OUTPUT_FILES.DXF: {
        language: f"gcs_{language.name.lower()}_{SUPPORTED_OUTPUT_FILES.DXF.name.lower()}_link"
        for language in SUPPORTED_LANGUAGES
    },
    SUPPORTED_OUTPUT_FILES.IFC: {SUPPORTED_LANGUAGES.EN: "gcs_en_ifc_link"},
}

GCS_DIRECTORY_BY_FILE_FORMAT = {
    SUPPORTED_OUTPUT_FILES.PNG: GOOGLE_CLOUD_RESULT_IMAGES,
    SUPPORTED_OUTPUT_FILES.PDF: GOOGLE_CLOUD_RESULT_IMAGES,
    SUPPORTED_OUTPUT_FILES.DXF: GOOGLE_CLOUD_DXF_FILES,
    SUPPORTED_OUTPUT_FILES.IFC: GOOGLE_CLOUD_SITE_IFC_FILES,
}

CLOUD_CONVERT_API_KEY = os.environ.get("CLOUD_CONVERT_API_KEY", "")
CLOUD_CONVERT_IS_SANDBOX = bool(
    strtobool(os.environ.get("CLOUD_CONVERT_IS_SANDBOX", "False"))
)
