from time import perf_counter


def start_timer() -> float:
    return perf_counter()


def elapsed_ms(start_time: float) -> float:
    return (perf_counter() - start_time) * 1000
