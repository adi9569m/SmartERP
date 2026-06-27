import unittest
from decimal import Decimal

from auth import hash_password, verify_password
from schemas import ValidationError, money, positive, require


class CoreTests(unittest.TestCase):
    def test_password_hashing(self):
        encoded = hash_password("correct horse")
        self.assertTrue(verify_password("correct horse", encoded))
        self.assertFalse(verify_password("wrong", encoded))

    def test_required_validation(self):
        with self.assertRaises(ValidationError):
            require({"name": ""}, "name")

    def test_numeric_validation(self):
        self.assertEqual(money("12.50", "amount"), Decimal("12.50"))
        with self.assertRaises(ValidationError):
            positive(0, "quantity")


if __name__ == "__main__":
    unittest.main()
