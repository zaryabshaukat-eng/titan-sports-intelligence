from datetime import datetime


def no_future_leakage(prediction_time: datetime, fixture_start: datetime) -> bool:
    return prediction_time <= fixture_start
