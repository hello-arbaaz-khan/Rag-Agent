# utils/response.py

from django.http import JsonResponse


def response_json(success=True, message="", data=None, errors=None, status=200):
    """
    Reusable function to build a consistent JSON response.

    Args:
        success (bool): Whether the request was successful.
        message (str): A human-readable message.
        data (dict|list|None): The payload to return.
        errors (dict|list|None): Error details, if any.
        status (int): HTTP status code.

    Returns:
        JsonResponse
    """
    response = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
    }

    if errors is not None:
        response["errors"] = errors

    return JsonResponse(response, status=status, safe=False)