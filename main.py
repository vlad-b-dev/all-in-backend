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

    # --- Prepara el contenido del correo personal ---
    if lang == "es":
        personal_subject = subject
        personal_message = f"Nuevo mensaje de {name} ({email}):\n\n{message}"
    else:
        personal_subject = subject
        personal_message = f"New message from {name} ({email}):\n\n{message}"

    # Envía a tu email
    send_email(TU_EMAIL, personal_subject, personal_message)

    # --- Prepara la confirmación al usuario ---
    if lang == "es":
        confirmation_subject = f"Confirmación de contacto: {subject}"
        confirmation_body = (
            f"Hola {name},\n\n"
            f"Hemos recibido tu mensaje sobre '{subject}':\n\n"
            f"{message}\n\n"
            "¡Gracias por contactar!"
        )
    else:
        confirmation_subject = f"Contact Confirmation: {subject}"
        confirmation_body = (
            f"Hi {name},\n\n"
            f"We have received your message regarding '{subject}':\n\n"
            f"{message}\n\n"
            "Thank you for getting in touch."
        )

    send_email(email, confirmation_subject, confirmation_body)
    return {"message": "Emails enviados correctamente"}
