from fastapi import HTTPException, status


class InvalidCredentialsException(HTTPException):
    """Email ou code invalide"""
    def __init__(self, detail: str = "Email ou code invalide"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class CodeExpiredException(HTTPException):
    """Code expiré"""
    def __init__(self, detail: str = "Code expiré, veuillez demander un nouveau code"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class UserNotVerifiedException(HTTPException):
    """Utilisateur non vérifié"""
    def __init__(self, detail: str = "Email non vérifié"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class BDENotCotisantException(HTTPException):
    """Utilisateur non cotisant BDE"""
    def __init__(self, detail: str = "Vous n'êtes pas cotisant BDE actif"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ReservationNotAllowedException(HTTPException):
    """Réservation non autorisée"""
    def __init__(self, detail: str = "Réservation non autorisée"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class AdminException(HTTPException):#a renomer TODO
    """Accès admin non autorisé"""
    def __init__(self, detail: str = "Vous devez être admin"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class EmailSendFailedException(HTTPException):
    """Envoi d'email échoué"""
    def __init__(self, detail: str = "Impossible d'envoyer l'email"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
