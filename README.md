# Bot Telegram — Rappels Kigurumi

Un petit bot en Python qui envoie 5 fois par jour un message pour te pousser à reprendre la confection de kigurumis.

Prérequis
- Python 3.9+ (pour zoneinfo)
- Crée un bot Telegram via BotFather et récupère le token.

Installation

Ouvre PowerShell et dans le dossier du projet :

```powershell
python -m pip install -r requirements.txt
```

Lancement via npm

Si tu préfères lancer le bot avec npm (pratique si tu as déjà npm pour d'autres scripts), j'ai ajouté un `package.json` qui exécute la commande Python :

```powershell
npm run start
```

Le script `npm test` lance `pytest`.

Configuration

Le projet supporte désormais un fichier `.env` pour centraliser la configuration (token, heures, timezone, fichier de messages).

1. Duplique `.env.example` en `.env` et remplis les valeurs :

```powershell
copy .env.example .env
# puis édite .env avec un éditeur de texte
```

Variables disponibles :
- `BOT_TOKEN` : token du bot Telegram (obligatoire)
- `TIMES` : heures séparées par des virgules (format HH:MM). Exemple : `08:00,11:30,14:00,17:00,20:00`. Valeur par défaut : `09:00,12:00,15:00,18:00,21:00`.
- `TIMEZONE` : fuseau (ex: `Europe/Paris`).
- `MESSAGES_FILE` : chemin vers le fichier JSON contenant la grande liste de messages (par défaut `messages.json`).
- `CHAT_ID` : (optionnel) id numérique d'un chat Telegram. Si défini, le bot enverra les rappels uniquement à ce chat (pratique si tu veux éviter d'envoyer /start depuis Telegram). Tu peux obtenir ton chat id en contactant `@userinfobot` ou en envoyant `/start` au bot et en regardant `chats.json` après l'inscription.
 - `CHAT_ID` : (optionnel) id numérique d'un chat Telegram. Si défini, le bot enverra les rappels uniquement à ce chat (pratique si tu veux éviter d'envoyer /start depuis Telegram). Tu peux obtenir ton chat id en contactant `@userinfobot` ou en envoyant `/start` au bot et en regardant `chats.json` après l'inscription.
 - `MENTION` : (optionnel) nom d'utilisateur à ajouter automatiquement à chaque message (par défaut `@nyerlazine`).

Utilisation

1. Lancer le bot :

```powershell
python main.py
```

2. Dans Telegram, ouvre ton bot et envoie `/start` pour t'inscrire.
3. Tu recevras 5 messages par jour aux heures configurées.
4. Envoie `/stop` pour arrêter de recevoir les messages.

Test rapide

```powershell
python -m pytest -q
```

Test d'envoi immédiat

Tu peux tester un envoi direct (sans attendre la planification) avec le script `send_now.py` :

```powershell
python send_now.py
# ou via npm
npm run send
```

Le script enverra le message soit au `CHAT_ID` défini dans `.env`, soit à tous les chats déjà enregistrés dans `chats.json` (après un `/start`).

Notes
- Le script conserve les identifiants de chat dans `chats.json`.
- Le bot doit rester en marche pour envoyer les notifications (exécutez-le sur un serveur ou une machine toujours allumée).

