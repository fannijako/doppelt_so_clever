from src.die import Die


def test_unrolled_die():
    die = Die("pink")
    assert not die.value


def test_rolled_die():
    die = Die("pink")
    die.roll()
    assert die.value is not None
    assert die.value >= 1
    assert die.value <= 6
