from fastapi import HTTPException, status


class DuplicateEmailExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_409_CONFLICT
        self.detail = "Email must be unique."


class DuplicatePhoneNumberExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_409_CONFLICT
        self.detail = "Phone number must be unique."
