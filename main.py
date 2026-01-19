#!/usr/bin/env python3
"""
Bot Telegram simple en Python qui envoie 5 rappels par jour pour refaire des kigurumis.
- Configurez BOT_TOKEN via la variable d'environnement BOT_TOKEN ou lancez /start dans Telegram.
- Le chat qui envoie /start sera enregistré et recevra les messages programmés.
- Configurez les heures via la variable TIMES (format HH:MM, séparées par des virgules).
- Configurez le fuseau via TIMEZONE (ex: Europe/Paris).
"""
import os
import json
import logging
import random
from datetime import time, datetime, timedelta
import threading
import time as time_mod
import requests
from zoneinfo import ZoneInfo
from typing import List

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# charge les variables depuis .env si présent
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHAT_FILE = os.path.join(os.path.dirname(__file__), "chats.json")

# configuration depuis .env (ou valeurs par défaut)
TIMES_ENV = os.getenv("TIMES")
DEFAULT_TIMES = [t.strip() for t in TIMES_ENV.split(",") if t.strip()] if TIMES_ENV else ["09:00", "12:00", "15:00", "18:00", "21:00"]
DEFAULT_TZ = os.getenv("TIMEZONE", "Europe/Paris")

# possibilité de surcharger le fichier des messages via .env
MESSAGES_FILE = os.path.join(os.path.dirname(__file__), os.getenv("MESSAGES_FILE", "messages.json"))
# qui mentionner (par défaut @nyerlazine)
MENTION = os.getenv("MENTION", "@nyerlazine")
# optionnel : id unique du chat à cibler (utile si tu veux envoyer sans faire /start)
CHAT_ID_ENV = os.getenv("CHAT_ID")

MESSAGES = [
    # remplaced by messages.json loader below
]


def load_messages() -> List[str]:
    """Charge la grande liste de messages depuis messages.json.

    Si le fichier est introuvable ou mal formé, on retourne une petite liste
    de secours intégrée.
    """
    fallback = [
        "C'est l'heure de créer un kigurumi ! Un petit pas aujourd'hui = un grand kigurumi demain 🧵🐻",
        "Replonge dans la couture — ton kigurumi n'attendra pas ! Fais-en un morceau aujourd'hui ✂️",
        "Besoin d'un push ? Pense à la joie que ton kigurumi apportera — 15 minutes suffisent pour avancer 😄",
    ]
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and all(isinstance(x, str) for x in data):
                    return data
    except Exception:
        logger.exception("Impossible de charger %s, utilisation du fallback", MESSAGES_FILE)
    return fallback


# charge les messages une fois
MESSAGES = load_messages()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chats() -> List[int]:
    if not os.path.exists(CHAT_FILE):
        return []
    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_chats(chat_ids: List[int]):
    try:
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(chat_ids, f)
    except Exception as e:
        logger.exception("Impossible d'enregistrer les chat ids: %s", e)


def make_message() -> str:
    base = random.choice(MESSAGES)
    # ajoute la mention à la fin du message (double saut de ligne pour lisibilité)
    return f"{base}\n\n{MENTION}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chats = load_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        save_chats(chats)
        await update.message.reply_text("Inscription reçue — vous recevrez maintenant les rappels pour refaire des kigurumis. 🎉")
        logger.info("Chat %s ajouté", chat_id)
    else:
        await update.message.reply_text("Vous êtes déjà inscrit pour recevoir les rappels.")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chats = load_chats()
    if chat_id in chats:
        chats.remove(chat_id)
        save_chats(chats)
        await update.message.reply_text("Vous ne recevrez plus les rappels. 🙏")
        logger.info("Chat %s supprimé", chat_id)
    else:
        await update.message.reply_text("Vous n'étiez pas inscrit.")


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /now : envoie immédiatement un message motivant dans le chat appelant."""
    try:
        text = make_message()
        # on répond directement à la commande avec le message
        await update.message.reply_text(text)
        logger.info("/now utilisé par chat %s", update.effective_chat.id)
    except Exception:
        logger.exception("Erreur lors du traitement de /now pour le chat %s", update.effective_chat.id)
        try:
            await update.message.reply_text("Impossible d'envoyer le message maintenant.")
        except Exception:
            pass


async def send_kigu(context: ContextTypes.DEFAULT_TYPE):
    """Callback planifié : envoie le message à tous les chats connus."""
    # si un CHAT_ID est défini dans .env, on l'utilise (envoi direct)
    if CHAT_ID_ENV:
        try:
            target = int(CHAT_ID_ENV)
        except Exception:
            logger.exception("CHAT_ID invalide dans .env: %s", CHAT_ID_ENV)
            return
        text = make_message()
        try:
            await context.bot.send_message(chat_id=target, text=text)
            logger.info("Message envoyé à CHAT_ID (depuis .env): %s", target)
        except Exception:
            logger.exception("Erreur en envoyant au CHAT_ID %s", target)
        return

    chats = load_chats()
    if not chats:
        logger.info("Aucun chat enregistré — aucun message envoyé.")
        return

    text = make_message()
    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            logger.info("Message envoyé à %s", chat_id)
        except Exception:
            logger.exception("Erreur en envoyant au chat %s", chat_id)


def schedule_jobs(app):
    tz = ZoneInfo(DEFAULT_TZ)
    # Préférence : utiliser JobQueue (requiert l'extra [job-queue]). Sinon, fallback en thread.
    if getattr(app, "job_queue", None):
        for t in DEFAULT_TIMES:
            try:
                hh, mm = [int(x) for x in t.strip().split(":" )]
                job_time = time(hour=hh, minute=mm, tzinfo=tz)
                app.job_queue.run_daily(send_kigu, job_time)
                logger.info("Job planifié chaque jour à %02d:%02d (%s) via JobQueue", hh, mm, DEFAULT_TZ)
            except Exception:
                logger.exception("Impossible de planifier l'heure: %s", t)
    else:
        logger.warning("JobQueue non disponible — démarrage du scheduler de secours en thread")
        token = os.getenv("BOT_TOKEN")

        def thread_scheduler(tok, times_list, tzname):
            tzlocal = ZoneInfo(tzname)
            base = f"https://api.telegram.org/bot{tok}"
            while True:
                now = datetime.now(tzlocal)
                next_runs = []
                for ts in times_list:
                    try:
                        hh2, mm2 = [int(x) for x in ts.strip().split(":" )]
                    except Exception:
                        continue
                    dt = datetime(now.year, now.month, now.day, hh2, mm2, tzinfo=tzlocal)
                    if dt <= now:
                        dt = dt + timedelta(days=1)
                    next_runs.append(dt)
                if not next_runs:
                    time_mod.sleep(60)
                    continue
                next_dt = min(next_runs)
                delta = (next_dt - now).total_seconds()
                logger.info("Scheduler de secours: attente %.0f secondes jusqu'à %s", delta, next_dt.isoformat())
                if delta > 0:
                    time_mod.sleep(delta)
                # envoi synchrone via HTTP
                chats = load_chats()
                if not chats:
                    logger.info("Aucun chat enregistré — scheduler de secours n'envoie rien.")
                    continue
                text = make_message()
                for chat_id in chats:
                    try:
                        resp = requests.post(f"{base}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=10)
                        logger.info("Scheduler de secours: envoi à %s status=%s", chat_id, getattr(resp, 'status_code', None))
                    except Exception:
                        logger.exception("Erreur lors de l'envoi par scheduler de secours au chat %s", chat_id)

        th = threading.Thread(target=thread_scheduler, args=(token, DEFAULT_TIMES, DEFAULT_TZ), daemon=True)
        th.start()


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERREUR: définissez la variable d'environnement BOT_TOKEN avec le token de votre bot Telegram.")
        print("Ou lancez le script et utilisez la commande /start depuis Telegram après avoir démarré l'application.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("now", now_command))

    schedule_jobs(app)

    logger.info("Démarrage du bot — écoute des commandes et envoi des rappels planifiés.")
    app.run_polling()


if __name__ == "__main__":
    main()
