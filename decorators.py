from time import time, sleep

class cached:
    def __init__(self, timeout_ms):
        self.timeout_ms = timeout_ms
        self.cache_time = -1
        self.cache_value = None

    def __call__(self, fn):
        def cached_fn(*args, **kwargs):
            if time() > self.cache_time:
                self.cache_value = fn(*args, **kwargs)
                self.cache_time = time() + (self.timeout_ms/1000.0)

            return self.cache_value
        return cached_fn

if __name__ == "__main__":
    @cached(500)
    def fn():
        return time()

    for i in range(0, 100):
        print(fn())
        sleep(0.1)
