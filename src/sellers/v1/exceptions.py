from fastapi import HTTPException, status


class StaffNotFoundExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "Staff not found."
