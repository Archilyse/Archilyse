from common_utils.logging_config import DefaultLogFormatter


class RequestId:
    """
    Simple object to store a unique task id within process context.
    """

    def __init__(self):
        self.rid = None

    def __str__(self):
        if self.rid is None:
            return ""
        return self.rid

    def set_id(self, new_id):
        """Sets the new id passed

        Args:
            new_id (str): with the celery uuid generated
        """
        self.rid = str(new_id)


global_current_request_id = RequestId()


class ApiLogFormatter(DefaultLogFormatter):
    def format(self, record):
        record.request_id = str(global_current_request_id)
        return super(ApiLogFormatter, self).format(record)
