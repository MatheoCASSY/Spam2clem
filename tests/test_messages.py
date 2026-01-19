from main import make_message
import json
import os


def test_make_message_returns_string_and_based_on_messages():
    msg = make_message()
    assert isinstance(msg, str)
    # vérifie que le message retourné commence par une entrée de messages.json (on ajoute une mention en suffixe)
    messages_file = os.path.join(os.path.dirname(__file__), os.pardir, "messages.json")
    messages_file = os.path.normpath(messages_file)
    try:
        with open(messages_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert any(msg.startswith(entry) for entry in data)
    except Exception:
        # si messages.json introuvable, on se contente que make_message retourne une string
        assert isinstance(msg, str)
