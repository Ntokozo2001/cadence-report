import os

import requests


class CCWConfigurationError(RuntimeError):
    pass


def _get_config():
    url = os.environ.get("CCW_GRAPHQL_URL", "").strip()
    token = os.environ.get("CCW_API_TOKEN", "").strip()
    if not url:
        raise CCWConfigurationError("CCW_GRAPHQL_URL is not configured")
    if not token:
        raise CCWConfigurationError("CCW_API_TOKEN is not configured")
    return url, token


def execute_ccw_graphql(query, variables=None, operation_name=None, timeout=30):
    url, token = _get_config()
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    if operation_name:
        payload["operationName"] = operation_name

    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data