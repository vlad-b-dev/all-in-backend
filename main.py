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
    allow_origins=["*"],  # Puedes poner tu dominio Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TU_EMAIL = os.getenv("TU_EMAIL")

def send_email(to_email, subject, body):
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

    # Email para ti
    personal_message = f"Nuevo mensaje de {name} ({email}):\n\n{message}"
    send_email(TU_EMAIL, "Nuevo mensaje de tu porfolio", personal_message)

    # Confirmación al usuario
    confirmation_message = f"Hola {name},\n\nHemos recibido tu mensaje:\n\n{message}\n\nGracias por contactar."
    send_email(email, "Confirmación de contacto", confirmation_message)

    return {"message": "Emails enviados correctamente"}
