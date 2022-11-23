class BaseSlamException(Exception):
    pass


class BaseElevationException(Exception):
    pass


class UserAuthorizationException(BaseSlamException):
    pass


class JWTSignatureExpiredException(BaseSlamException):
    pass


class SiteCheckException(BaseSlamException):
    pass


class DBValidationException(BaseSlamException):
    pass


class GCSLinkEmptyException(BaseSlamException):
    pass


class OverpassAPIException(BaseSlamException):
    pass


class GoogleGeocodeAPIException(BaseSlamException):
    pass


class ValidationException(BaseSlamException):
    pass


class QAValidationException(BaseSlamException):
    pass


class QAMissingException(BaseSlamException):
    def __init__(self, *args, site_id=None):
        self.site_id = site_id
        super().__init__(*args)


class DependenciesUnMetSimulationException(BaseSlamException):
    pass


class DBNotFoundException(BaseSlamException):
    pass


class DBMultipleResultsException(BaseSlamException):
    pass


class FeaturesGenerationException(BaseSlamException):
    pass


class CorruptedAnnotationException(BaseSlamException):
    pass


class TaskAlreadyRunningException(BaseSlamException):
    pass


class BasicFeaturesException(BaseSlamException):
    def __init__(self, *args, violations=None):
        self.violations = violations
        super().__init__(args)


class InvalidImage(BaseSlamException):
    pass


class InvalidRegion(BaseSlamException):
    def __init__(self, x: float, y: float, msg: str = None):
        self.message = msg or f"Coords {x}, {y} are not within any supported region"


class BrooksException(Exception):
    pass


class LayoutTriangulationException(BaseSlamException):
    pass


class AreaMismatchException(BaseSlamException):
    """Raised when the provided area ids cannot be resolved in the units of applicable plan"""

    pass


class BasicFeatureValidationException(BasicFeaturesException):
    pass


class BasePotentialViewException(BaseSlamException):
    pass


class MissingTargetPotentialException(BasePotentialViewException):
    pass


class DBException(BaseSlamException):
    pass


class UnsupportedDBModelException(Exception):
    pass


class NonExistingViewResultsException(Exception):
    pass


class InvalidShapeException(Exception):
    pass


class QuavisSimulationException(BaseSlamException):
    pass


class RectangleNotCalculatedException(BaseSlamException):
    pass


class SimulationNotSuccessException(Exception):
    pass


class NoEntitiesFileException(BaseSlamException):
    pass


class NotEnoughTrainingDataClassifierException(Exception):
    pass


class NoClassifierAvailableException(Exception):
    pass


class InaccurateClassifierException(Exception):
    pass


class SendGridMailException(BaseSlamException):
    pass


class ConnectivityEigenFailedConvergenceException(BaseSlamException):
    pass


class SurroundingException(BaseSlamException):
    pass


class RasterNotIntersectingException(BaseSlamException):
    pass


class CompetitionFeaturesValueError(BaseSlamException):
    pass


class CompetitionConfigurationMissingError(BaseSlamException):
    pass


class GCloudStorageException(BaseSlamException):
    pass


class GCloudMissingBucketException(BaseSlamException):
    pass


class NoiseLayoutUnclassifiedException(BaseSlamException):
    pass


class MissingSunDimensionException(BaseSlamException):
    pass


class WallPostProcessorException(BaseSlamException):
    pass


class NetAreaDistributionUnsetException(BaseSlamException):
    pass


class OpenTopoException(BaseSlamException):
    pass


class BuildingSegmentNotFoundException(BaseSlamException):
    pass


class CloudConvertException(BaseSlamException):
    pass


class CloudConvertUploadException(CloudConvertException):
    pass


class CloudConvertConvertException(CloudConvertException):
    pass


class CloudConvertExportException(CloudConvertException):
    pass


class ReactAnnotationMigrationException(BaseSlamException):
    pass


class AngleInferenceException(BaseSlamException):
    pass


class BulkVolumeVolumeException(BaseSlamException):
    pass


class OutOfGridException(BaseSlamException):
    pass


class OpeningTooSmallException(BaseSlamException):
    pass


class IfcEmptyStoreyException(BaseSlamException):
    pass


class IfcMappingException(BaseSlamException):
    pass


class PHResultVectorValidationException(BaseSlamException):
    pass


class DXFImportException(BaseSlamException):
    pass


class ShapelyToReactMappingException(BaseSlamException):
    pass


class RasterWindowNoDataException(BaseSlamException):
    pass


class PHVectorSubgroupException(BaseSlamException):
    pass
