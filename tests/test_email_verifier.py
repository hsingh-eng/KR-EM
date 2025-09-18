import unittest
from src.email_verifier import EmailVerifier

class TestEmailVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = EmailVerifier()

    def test_valid_email_format(self):
        valid_emails = [
            "test@example.com",
            "user.name@domain.com",
            "user+tag@domain.co.uk"
        ]
        for email in valid_emails:
            self.assertTrue(self.verifier.is_valid_format(email))

    def test_invalid_email_format(self):
        invalid_emails = [
            "invalid.email",
            "@nodomain.com",
            "no@domain@here.com",
            "spaces in@domain.com"
        ]
        for email in invalid_emails:
            self.assertFalse(self.verifier.is_valid_format(email))

if __name__ == '__main__':
    unittest.main()