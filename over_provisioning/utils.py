import time


def pinpoint_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        func_execution_time = end_time - start_time
        return result, func_execution_time

    return wrapper
