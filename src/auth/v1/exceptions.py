from fastapi import HTTPException, status


class DuplicateEmailExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Email must be unique."


class DuplicatePhoneNumberExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Phone number must be unique."
