from src.auth.v1 import utils


def send_verification_code() -> str:
    # Verification code must be exact 6 digits.
    return utils.generate_random_code(6)
