import unittest

from scripts.rounding import mix_bounds


class RoundingBoundsTests(unittest.TestCase):
    def test_two_types_with_known_extrema(self):
        # The fast-rising type gains 49.9–50.1 percentage points.
        # The rates can differ by 99–101 g/mi.
        low, high = mix_bounds([75, 25], [25, 75], [100, 200], [100, 200])
        self.assertAlmostEqual(low, 0.499 * 99)
        self.assertAlmostEqual(high, 0.501 * 101)

    def test_rejects_percentages_that_cannot_add_to_100(self):
        with self.assertRaisesRegex(ValueError, "totaling 100%"):
            mix_bounds([50, 45], [50, 50], [100, 200], [100, 200])
