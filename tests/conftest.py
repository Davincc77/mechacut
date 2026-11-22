import sys
sys.path.insert(0, ".")


def pytest_runtest_setup(item):
    # the cache is process-global test state; per-test isolation keeps the
    # payments suite (identical bodies across cases) deterministic
    import cache
    cache.clear()
