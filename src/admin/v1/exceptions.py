from fastapi import HTTPException, status


class ProviderNotFoundExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "There is no provider with the provided info."


class ProviderAlreadyIsActiveExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Provider is already active."
