def no_future_leakage(prediction_time: object, fixture_start: object) -> bool:
    return prediction_time <= fixture_start
