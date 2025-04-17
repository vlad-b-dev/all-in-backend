from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TU_EMAIL = os.getenv("TU_EMAIL")


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str
    subject: str = "Consulta desde tu portafolio"
    lang: str = "en"


def send_email(to_email: str, subject: str, body: str):
    """Envía un correo simple en texto plano."""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email enviado a {to_email} con asunto '{subject}'")
    except Exception as e:
        logger.error(f"Error al enviar email a {to_email}: {e}")


@app.post("/contact")
async def contact(
    payload: ContactRequest,
    background_tasks: BackgroundTasks
):
    if "@" not in payload.email:
        raise HTTPException(status_code=400, detail="Email inválido")

    lang = payload.lang.lower()

    server_subject = f"All-in Request - {payload.subject}"
    server_body = (
        f"{'Nuevo mensaje' if lang=='es' else 'New message'} de "
        f"{payload.name} ({payload.email}):\n\n{payload.message}"
    )

    if lang == "es":
        confirmation_subject = f"Mensaje recibido: {payload.subject}"
        confirmation_body = (
            f"Hola {payload.name},\n\n"
            "Hemos recibido tu mensaje:\n\n"
            f"\"Asunto\": \"{payload.subject}\"\n"
            f"\"Mensaje\": \"{payload.message}\"\n\n"
            "¡En breve contactaremos contigo! - All-in"
        )
    else:
        confirmation_subject = f"Contact Confirmation: {payload.subject}"
        confirmation_body = (
            f"Hi {payload.name},\n\n"
            "We have received your message:\n\n"
            f"\"Subject\": \"{payload.subject}\"\n"
            f"\"Message\": \"{payload.message}\"\n\n"
            "We will contact you soon! - All-in"
        )

    background_tasks.add_task(send_email, TU_EMAIL, server_subject, server_body)
    background_tasks.add_task(send_email, payload.email, confirmation_subject, confirmation_body)

    return {"message": "Emails en proceso de envío"}
