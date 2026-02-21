tasks = {}
languages = {}

def get_key(chat_id):
    return chat_id

def get_lang(chat_id):
    return languages.get(chat_id, "ru")

def set_lang(chat_id, lang):
    languages[chat_id] = lang

def add_task(chat_id, text):
    tasks.setdefault(chat_id, []).append(text)

def get_tasks(chat_id):
    return tasks.get(chat_id, [])
