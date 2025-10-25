import pytest
from under_test import power

@pytest.mark.parametrize("base, exponent, expected", [
    (2, 3, 8),
    (5, 0, 1),
    (3, 1, 3),
    (-2, 3, -8),
    (2, -1, 0.5),
    (1.5, 2, 2.25),
    (0, 5, 0),
    (10, -2, 0.01),
])
def test_power(base, exponent, expected):
    assert power(base, exponent) == pytest.approx(expected)

def test_power_type_errors():
    with pytest.raises(TypeError):
        power("2", 3)
    with pytest.raises(TypeError):
        power(2, "3")
    with pytest.raises(TypeError):
        power(None, 0)