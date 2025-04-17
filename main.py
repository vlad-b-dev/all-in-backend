from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS para conectar desde tu frontend en Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta a tu dominio Vercel si lo deseas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TU_EMAIL = os.getenv("TU_EMAIL")


def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


@app.post("/contact")
async def contact(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")
    subject = data.get("subject", "Consulta desde tu portafolio")
    lang = data.get("lang", "en").lower()

    server_subject = f"All-in Request - {subject}"
    if lang == "es":
        server_body = f"Nuevo mensaje de {name} ({email}):\n\n{message}"
    else:
        server_body = f"New message from {name} ({email}):\n\n{message}"

    send_email(TU_EMAIL, server_subject, server_body)

    if lang == "es":
        confirmation_subject = f"Mensaje recibido: {subject}"
        confirmation_body = (
            f"Hola {name},\n\n"
            "Hemos recibido tu mensaje:\n\n"
            f"\"Asunto\": \"{subject}\"\n"
            f"\"Mensaje\": \"{message}\"\n\n"
            "¡En breve contactaremos con usted! - All-in"
        )
    else:
        confirmation_subject = f"Contact Confirmation: {subject}"
        confirmation_body = (
            f"Hi {name},\n\n"
            "We have received your message:\n\n"
            f"\"Subject\": \"{subject}\"\n"
            f"\"Message\": \"{message}\"\n\n"
            "We will contact you soon! - All-in"
        )

    # Envía confirmación al usuario
    send_email(email, confirmation_subject, confirmation_body)

    return {"message": "Emails enviados correctamente"}
