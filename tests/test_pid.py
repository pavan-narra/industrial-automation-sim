from src.pid_control import PIDController

def test_pid_response():
    pid = PIDController(1.0, 0.1, 0.05, setpoint=50)
    output = pid.compute(measured_value=45, dt=1)
    assert isinstance(output, float)
    assert output > 0
