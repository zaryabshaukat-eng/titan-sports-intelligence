class RiskError(Exception):
    pass


class RiskResolutionError(RiskError):
    pass


class RiskVersionConflictError(RiskError):
    pass


class RiskValidationError(RiskError):
    pass
