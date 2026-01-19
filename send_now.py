#!/usr/bin/env python3
"""Envoie un message immédiatement pour tests.

Usage: configure .env (BOT_TOKEN et CHAT_ID ou avoir des chats enregistrés via /start), puis:
    python send_now.py

Le script choisit un message aléatoire depuis messages.json (ou fallback) et l'envoie.
"""
import os
import json
import random
import logging
from typing import List

from dotenv import load_dotenv
import requests

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HERE = os.path.dirname(__file__)
CHAT_FILE = os.path.join(HERE, "chats.json")
MESSAGES_FILE = os.path.join(HERE, os.getenv("MESSAGES_FILE", "messages.json"))


def load_messages() -> List[str]:
    fallback = [
        "C'est l'heure de créer un kigurumi ! Un petit pas aujourd'hui = un grand kigurumi demain 🧵🐻",
        "Replonge dans la couture — ton kigurumi n'attendra pas ! Fais-en un morceau aujourd'hui ✂️",
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


def load_chats() -> List[int]:
    if not os.path.exists(CHAT_FILE):
        return []
    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        logger.exception("Impossible de charger %s", CHAT_FILE)
    return []


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERREUR: définissez BOT_TOKEN dans .env")
        return

    # vérifie rapidement le token via l'API HTTP (getMe)
    base = f"https://api.telegram.org/bot{token}"
    try:
        r = requests.get(f"{base}/getMe", timeout=10)
        r.raise_for_status()
        me = r.json()
        if not me.get("ok"):
            print("Token invalide ou erreur getMe:", me)
            return
        username = me["result"].get("username")
        bot_id = me["result"].get("id")
        print(f"Connecté en tant que @{username} (id={bot_id})")
    except Exception as e:
        print("Impossible d'authentifier le token:", type(e).__name__, e)
        return
    messages = load_messages()
    message_base = random.choice(messages)
    mention = os.getenv("MENTION", "@nyerlazine")
    text = f"{message_base}\n\n{mention}"

    chat_id_env = os.getenv("CHAT_ID")
    targets = []
    if chat_id_env:
        try:
            targets = [int(chat_id_env)]
        except Exception:
            print("CHAT_ID invalide dans .env")
            return
    else:
        targets = load_chats()

    if not targets:
        print("Aucun destinataire trouvé. Soit définis CHAT_ID dans .env, soit envoie /start au bot depuis Telegram pour t'enregistrer.")
        return

    for t in targets:
        try:
            payload = {"chat_id": t, "text": text}
            r = requests.post(f"{base}/sendMessage", data=payload, timeout=10)
            r.raise_for_status()
            resp = r.json()
            if not resp.get("ok"):
                print(f"Erreur API lors de l'envoi au chat {t}:", resp)
            else:
                print(f"Message envoyé à {t}")
        except Exception as e:
            # affiche l'erreur en clair pour le debug
            print(f"Erreur en envoyant au chat {t}: {type(e).__name__}: {e}")
            logger.exception("Erreur en envoyant au chat %s: %s", t, e)


if __name__ == "__main__":
    main()
