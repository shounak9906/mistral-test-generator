import pytest
from under_test import power

@pytest.mark.parametrize("base, exponent, expected", [
    (2, 3, 8),
    (5, 0, 1),
    (3, 1, 3),
    (-2, 3, -8),
    (2, -3, 0.125),
    (1.5, 2, 2.25),
    (0, 5, 0),
    (10, -1, 0.1),
    (9, 0.5, 3.0),
])
def test_power(base, exponent, expected):
    result = power(base, exponent)
    assert result == pytest.approx(expected)

def test_power_with_invalid_exponent():
    with pytest.raises(TypeError):
        power(2, "invalid")