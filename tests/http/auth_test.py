async def test_all_endpoints_give_401_with_bad_csrf_token(
    fixt_client, fixt_http_all_endpoints, fixt_http_headers_testy, fixt_forged_csrf_token
):
    """All http endpoints should return a 401 if accessed with a forced CSRF token."""

    url, method = fixt_http_all_endpoints
    bad_csrf_headers = {
        "Authorization": fixt_http_headers_testy["Authorization"],
        "X-CSRF-TOKEN": fixt_forged_csrf_token,
    }
    res = await getattr(fixt_client, method.lower())(url, headers=bad_csrf_headers)
    assert res.status_code == 401


async def test_secured_endpoints_require_auth(
    fixt_client, fixt_http_secure_endpoints, fixt_http_headers_testy
):
    """All authenticated http endpoints should return a 401 response if accessed
    without a valid user token."""

    url, method = fixt_http_secure_endpoints
    bad_auth_headers = {
        "Authorization": "Bearer invalid_token",
        "X-CSRF-TOKEN": fixt_http_headers_testy["X-CSRF-TOKEN"],
    }
    res = await getattr(fixt_client, method.lower())(url, headers=bad_auth_headers)
    assert res.status_code == 401


async def test_401_with_incorrect_token_format(
    fixt_client, fixt_http_secure_endpoints, fixt_testy, fixt_http_headers_testy
):
    """All authenticated http endpoints should return a 401 response if accessed
    with an incorrectly formatted user token."""

    url, method = fixt_http_secure_endpoints
    bad_auth_headers = {
        "Authorization": (await fixt_testy()).hashed_token.token,
        "X-CSRF-TOKEN": fixt_http_headers_testy["X-CSRF-TOKEN"],
    }
    res = await getattr(fixt_client, method.lower())(url, headers=bad_auth_headers)
    assert res.status_code == 401


async def test_401_with_malformed_bearer_token(
    fixt_client, fixt_http_secure_endpoints, fixt_http_headers_testy
):
    """All authenticated http endpoints should return a 401 response if accessed
    with a malformed user token."""

    url, method = fixt_http_secure_endpoints
    bad_auth_headers = {
        "Authorization": "short",
        "X-CSRF-TOKEN": fixt_http_headers_testy["X-CSRF-TOKEN"],
    }

    res = await getattr(fixt_client, method.lower())(url, headers=bad_auth_headers)
    assert res.status_code == 401


async def test_401_with_missing_auth_header(
    fixt_client, fixt_http_secure_endpoints, fixt_http_headers_csrf_only
):
    """All authenticated http endpoints should return a 401 response if accessed
    without an Authorization header."""

    url, method = fixt_http_secure_endpoints
    res = await getattr(fixt_client, method.lower())(url, headers=fixt_http_headers_csrf_only)
    assert res.status_code == 401


async def test_401_with_missing_csrf_header(
    fixt_client, fixt_http_all_endpoints, fixt_http_headers_testy
):
    """All endpoints should return a 401 response if accessed
    without a csrf header."""

    url, method = fixt_http_all_endpoints
    res = await getattr(fixt_client, method.lower())(
        url, headers={"Authorization": fixt_http_headers_testy["Authorization"]}
    )
    assert res.status_code == 401
