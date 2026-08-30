from security_monitoring import SlidingWindowLimiter


def test_request_limiter_allows_requests_under_limit():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    assert limiter.allowed("client") is True
    assert limiter.allowed("client") is True
    assert limiter.allowed("client") is False


def test_request_limiter_isolated_by_client_key():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    assert limiter.allowed("client-a") is True
    assert limiter.allowed("client-a") is False
    assert limiter.allowed("client-b") is True
