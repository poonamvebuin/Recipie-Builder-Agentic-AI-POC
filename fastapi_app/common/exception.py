from builtins import Exception

__all__ = [
    "BadRequestException",
    "InsufficientPermissionsException",
    "ResourceNotFoundException",
]


class BadRequestException(Exception):
    pass


class InsufficientPermissionsException(Exception):
    pass


class ResourceNotFoundException(Exception):
    pass
