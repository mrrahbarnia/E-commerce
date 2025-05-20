from fastapi import HTTPException, status


class UserNotFoundExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "Account not found."


class AccountNotActiveForInvitationExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Account is not active for invitation."


class CannotInviteProviderExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Cannot invite providers."


class SellerStaffUniqueExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Each seller can invite a user only once."


class StaffAlreadyAtWorkExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "This user is already working for another provider."


class ProviderAlreadyInviteUserExc(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Each provider can invite a user only once."
