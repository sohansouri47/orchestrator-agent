from fastapi import Request

def get_headers(request: Request) -> dict[str, str]:
    """Get Headers for requests

    Args:
        request (Request): The FastAPI request object.

    Returns:
        dict[str, str]: A dictionary containing the headers from the request.
    """
    return request.headers