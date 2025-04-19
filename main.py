from fastapi import FastAPI, BackgroundTasks, HTTPException
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


def _send_email_raw(to_email: str, subject: str, body: str, is_html: bool = False):
    """Base: dispara el SMTP y lanza la excepción si falla."""
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
    """Para tareas en background: atrapa errores y los loggea."""
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

    # Prepare HTML-safe message (no backslashes inside f-strings)
    html_message = payload.message.replace("\n", "<br>")

    # ---- Rich HTML layout for admin notification ----
    server_body = f"""
    <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.4;">
      <h2 style="margin-bottom: 0.5em;">
        {'📬 Nuevo mensaje recibido' if lang=='es' else '📬 New Message Received'}
      </h2>
      <table style="width: 100%; border-collapse: collapse; margin-top: 1em;">
        <tr>
          <td style="padding: 8px; font-weight: bold; width: 120px;">{ 'Nombre' if lang=='es' else 'Name' }:</td>
          <td style="padding: 8px;">{payload.name}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 8px; font-weight: bold;">Email:</td>
          <td style="padding: 8px;">{payload.email}</td>
        </tr>
        <tr>
          <td style="padding: 8px; font-weight: bold;">{ 'Asunto' if lang=='es' else 'Subject' }:</td>
          <td style="padding: 8px;">{payload.subject}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 8px; font-weight: bold; vertical-align: top;">{ 'Mensaje' if lang=='es' else 'Message' }:</td>
          <td style="padding: 8px;">{html_message}</td>
        </tr>
      </table>
      <p style="margin-top: 1.5em; font-size: 0.9em; color: #666;">
        { 'Enviado desde tu portafolio All‑in' if lang=='es' else 'Sent from your All‑in portfolio' }
      </p>
    </div>
    """

    # ---- Rich HTML layout for client confirmation ----
    if lang == "es":
        confirmation_subject = f"Mensaje recibido: {payload.subject}"
        confirmation_body = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
          <h2 style="color: #2a7ae2; margin-bottom: 0.5em;">✅ Confirmación de recibido</h2>
          <p>¡Hola {payload.name}!</p>
          <p><strong>Hemos recibido tu mensaje</strong> y estaremos en contacto contigo pronto.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 1em 0;" />
          <p><strong>Asunto:</strong> {payload.subject}</p>
          <p><strong>Mensaje:</strong></p>
          <p style="margin-left:1em; color: #555;">{html_message}</p>
          <p style="margin-top: 1.5em; font-size: 0.9em; color: #666;">
            Gracias por escribirnos. | All‑in
          </p>
        </div>
        """
    else:
        confirmation_subject = f"Contact Confirmation: {payload.subject}"
        confirmation_body = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
          <h2 style="color: #2a7ae2; margin-bottom: 0.5em;">✅ Your message has been received</h2>
          <p>Hi {payload.name},</p>
          <p><strong>We have received your message</strong> and will get back to you soon.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 1em 0;" />
          <p><strong>Subject:</strong> {payload.subject}</p>
          <p><strong>Message:</strong></p>
          <p style="margin-left:1em; color: #555;">{html_message}</p>
          <p style="margin-top: 1.5em; font-size: 0.9em; color: #666;">
            Thanks for reaching out! | All‑in
          </p>
        </div>
        """

    # Send confirmation email as HTML
    try:
        _send_email_raw(payload.email, confirmation_subject, confirmation_body, is_html=True)
        logger.info(f"Confirmación enviada a {payload.email}")
    except Exception as e:
        logger.error(f"Error enviando confirmación a {payload.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar la confirmación al cliente"
        )

    # Send admin notification in background as HTML
    background_tasks.add_task(
        send_email_background,
        TU_EMAIL,
        server_subject,
        server_body,
        True
    )

    return {"message": "Confirmación enviada. Tu solicitud ha sido recibida."}
