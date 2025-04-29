__all__ = ["errors"]

errors = {
    "Exception":{},

    "BadRequestException": {
        "ok": False,
        "error": "BAD_REQUEST",
        "message": "",
        "status": 400,
    },
    "InsufficientPermissionsException": {
        "ok": False,
        "error": "INSUFFICIENT_PERMISSIONS",
        "message": "Insufficient Permissions",
        "status": 403,
    },
    "ResourceNotFoundException": {
        "ok": False,
        "error": "RESOURCE_NOT_FOUND",
        "message": "Resource not found",
        "status": 404,
    },

}
