def check_sensor_range(value, low=0, high=100):
    """Check if a sensor value is valid."""
    if value is None:
        return False
    return low <= value <= high
