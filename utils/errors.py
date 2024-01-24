class GTFSAPIError(RuntimeError):
    """ An error occurred when requesting data from the GTFS API """
    def __init__(self, text=None, error_place: str = None):
        # error_place = whether the error occurred at real-time data or vehicle data
        super().__init__(text)
        self.error_place = error_place
