from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

from mail import send_test_email

class EmailSchema(BaseModel):
    email: List[EmailStr]


app = FastAPI(root_path="/api")



@app.post("/email")
async def simple_send(email: EmailSchema) -> JSONResponse:
    for email in email.email:
        await send_test_email(email)
    return JSONResponse(status_code=200, content={"message": "Emails sent"})
