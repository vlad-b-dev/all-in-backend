from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from dotenv import load_dotenv
import html

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

# Paleta de colores
COLORS = {
    "main": "#efc847",
    "hover": "#181818",
    "highlight": "#0057d9",
    "bg_main": "#d6d6d6",
    "bg_secondary": "#ffffff",
}

def _send_email_raw(to_email: str, subject: str, body: str, is_html: bool = False):
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html" if is_html else "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

def send_email_background(to_email: str, subject: str, body: str, is_html: bool = False):
    try:
        _send_email_raw(to_email, subject, body, is_html)
        logger.info(f"[BG] Email enviado a {to_email} con asunto '{subject}'")
    except Exception as e:
        logger.error(f"[BG] Error enviando a {to_email}: {e}")

@app.post("/contact")
async def contact(payload: ContactRequest, background_tasks: BackgroundTasks):
    if "@" not in payload.email:
        raise HTTPException(status_code=400, detail="Email inválido")

    lang = payload.lang.lower()
    server_subject = f"All-in Request - {payload.subject}"

    # Escapar el mensaje para evitar inyección HTML
    escaped_message = html.escape(payload.message).replace("\n", "<br>")

    # Cuerpo del email al administrador
    server_body = f"""
    <div style="font-family: Arial, sans-serif; background-color: {COLORS['bg_main']}; padding: 20px; border-radius: 10px;">
      <h2 style="margin-bottom: 0.5em; color: {COLORS['highlight']};">
        {'📬 Nuevo mensaje recibido' if lang=='es' else '📬 New Message Received'}
      </h2>
      <table style="width: 100%; border-collapse: collapse; margin-top: 1em; background-color: {COLORS['bg_secondary']}; border-radius: 8px;">
        <tr>
          <td style="padding: 8px; font-weight: bold; width: 120px; color: {COLORS['main']};">{ 'Nombre' if lang=='es' else 'Name' }:</td>
          <td style="padding: 8px; color: #333;">{payload.name}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 8px; font-weight: bold; color: {COLORS['main']};">Email:</td>
          <td style="padding: 8px; color: #333;">{payload.email}</td>
        </tr>
        <tr>
          <td style="padding: 8px; font-weight: bold; color: {COLORS['main']};">{ 'Asunto' if lang=='es' else 'Subject' }:</td>
          <td style="padding: 8px; color: #333;">{payload.subject}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 8px; font-weight: bold; color: {COLORS['main']}; vertical-align: top;">{ 'Mensaje' if lang=='es' else 'Message' }:</td>
          <td style="padding: 8px; color: #333;">{escaped_message}</td>
        </tr>
      </table>
      <p style="margin-top: 1.5em; font-size: 0.9em; color: #666;">
        { 'Enviado desde tu portafolio All‑in' if lang=='es' else 'Sent from your All‑in portfolio' }
      </p>
    </div>
    """

    # Cuerpo del email de confirmación al cliente (mejorado con estilo vibrante)
    if lang == "es":
        confirmation_subject = f"Mensaje recibido: {payload.subject}"
        confirmation_body = f"""
        <div style="font-family: Arial, sans-serif; background-color: {COLORS['bg_secondary']}; padding: 30px; border-radius: 12px; border: 2px solid {COLORS['main']}; max-width: 600px; margin: auto;">
          <h1 style="color: {COLORS['main']}; margin-bottom: 0.5em; font-size: 24px;">✅ Mensaje recibido</h1>
          <p style="font-size: 16px; color: #333;">¡Hola <strong>{payload.name}</strong>!</p>
          <p style="font-size: 14px; color: #555; line-height: 1.5;"><strong>Hemos recibido tu mensaje</strong> y nos pondremos en contacto contigo pronto.</p>
          <div style="margin: 20px 0; padding: 15px; background-color: {COLORS['bg_main']}; border-radius: 8px;">
            <p style="margin: 0; font-weight: bold; color: {COLORS['highlight']};">Asunto:</p>
            <p style="margin: 5px 0 0 0; color: #333;">{payload.subject}</p>
            <p style="margin: 15px 0 5px 0; font-weight: bold; color: {COLORS['highlight']};">Mensaje:</p>
            <p style="margin: 0; color: #333; line-height: 1.4;">{escaped_message}</p>
          </div>
          <a href="https://all-in-dev.vercel.app" style="display: inline-block; text-decoration: none; background-color: {COLORS['highlight']}; color: #fff; padding: 10px 20px; border-radius: 6px; font-weight: bold;">All-in</a>
          <p style="margin-top: 20px; font-size: 12px; color: #999;">¡Gracias por contactar!</p>
        </div>
        """
    else:
        confirmation_subject = f"Contact Confirmation: {payload.subject}"
        confirmation_body = f"""
        <div style="font-family: Arial, sans-serif; background-color: {COLORS['bg_secondary']}; padding: 30px; border-radius: 12px; border: 2px solid {COLORS['main']}; max-width: 600px; margin: auto;">
          <h1 style="color: {COLORS['main']}; margin-bottom: 0.5em; font-size: 24px;">✅ Your message has been received</h1>
          <p style="font-size: 16px; color: #333;">Hi <strong>{payload.name}</strong>,</p>
          <p style="font-size: 14px; color: #555; line-height: 1.5;"><strong>We have received your message</strong> and will get back to you soon.</p>
          <div style="margin: 20px 0; padding: 15px; background-color: {COLORS['bg_main']}; border-radius: 8px;">
            <p style="margin: 0; font-weight: bold; color: {COLORS['highlight']};">Subject:</p>
            <p style="margin: 5px 0 0 0; color: #333;">{payload.subject}</p>
            <p style="margin: 15px 0 5px 0; font-weight: bold; color: {COLORS['highlight']};">Message:</p>
            <p style="margin: 0; color: #333; line-height: 1.4;">{escaped_message}</p>
          </div>
          <a href="https://all-in-dev.vercel.app/" style="display: inline-block; text-decoration: none; background-color: {COLORS['highlight']}; color: #fff; padding: 10px 20px; border-radius: 6px; font-weight: bold;">All-in</a>
          <p style="margin-top: 20px; font-size: 12px; color: #999;">Thanks for reaching out!</p>
        </div>
        """

    # Enviar confirmación al cliente
    try:
        _send_email_raw(payload.email, confirmation_subject, confirmation_body, is_html=True)
        logger.info(f"Confirmación enviada a {payload.email}")
    except Exception as e:
        logger.error(f"Error enviando confirmación a {payload.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar la confirmación al cliente"
        )

    # Notificación al admin en background
    background_tasks.add_task(
        send_email_background,
        TU_EMAIL,
        server_subject,
        server_body,
        True
    )

    return {"message": "Confirmación enviada. Tu solicitud ha sido recibida."}
