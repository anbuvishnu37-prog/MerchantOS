from app.payment.simulator import simulate_payment
from app.payment.state_machine import PaymentState


def test_simulator_success():
    result = simulate_payment("success")
    assert result == PaymentState.PAID


def test_simulator_failure():
    result = simulate_payment("failure")
    assert result == PaymentState.FAILED


def test_simulator_timeout():
    result = simulate_payment("timeout")
    assert result == PaymentState.UNKNOWN


def test_simulator_invalid_scenario():
    try:
        simulate_payment("invalid")
        assert False
    except ValueError:
        assert True