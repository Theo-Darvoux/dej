from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from .markdown import generate_markdown_for_all_clients, markdown_2_pdf
from ..users.router import get_current_user_from_cookie
from ..core.exceptions import AdminException
from ..db.session import get_db

router = APIRouter(tags=["print"])


@router.get("/get_printPDF")
def get_ticket_pdf(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    # Vérifier si l'utilisateur est admin
    if current_user.admin != "admin":
        raise AdminException()
    
    # Générer le markdown et le PDF
    markdown_example = generate_markdown_for_all_clients([0, 1, 2])    
    pdf_bytes = markdown_2_pdf(markdown_example)

    # Retourner le PDF en tant que réponse
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=ticket.pdf"
        }
    )
