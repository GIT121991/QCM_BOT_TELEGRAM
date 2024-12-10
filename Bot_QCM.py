import matplotlib.pyplot as plt
import io
import asyncpg
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import os
from flask import Flask
import threading

# Lancer le serveur Flask pour écouter un port fictif
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Telegram actif !"

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Render utilise une variable d'environnement PORT
    app.run(host="0.0.0.0", port=port)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in the environment variables.")

# États du bot
REGISTER, THEMES, QUESTION = range(3)

# Configuration PostgreSQL
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "postgres"),
    "port": int(os.getenv("DB_PORT", 5432)),
}

# Fonction pour établir une connexion
async def get_connection():
    return await asyncpg.connect(**db_config)

# Fonction générique pour exécuter des requêtes SQL
async def execute_query(query, params=None, fetchone=False):
    conn = await get_connection()
    try:
        if fetchone:
            result = await conn.fetchrow(query, *params)
        else:
            result = await conn.fetch(query, *params)
        return result
    except Exception as e:
        print(f"Erreur PostgreSQL : {e}")
        return None
    finally:
        await conn.close()

# Démarrage du bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bienvenue au QCM ! Veuillez entrer votre nom pour commencer.")
    return REGISTER

# Enregistrement de l'utilisateur
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    telegram_id = update.message.from_user.id

    await execute_query(
        """
        INSERT INTO users (telegram_id, name)
        VALUES ($1, $2)
        ON CONFLICT (telegram_id)
        DO UPDATE SET name = EXCLUDED.name, score = 0, current_question = 0
        """,
        (telegram_id, name)
    )

    await update.message.reply_text(f"Merci {name} ! Préparons-nous pour le QCM.")
    return await choose_theme(update, context)

# Afficher les thèmes disponibles et permettre à l'utilisateur de choisir
async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    themes = await execute_query(
        "SELECT id, name FROM themes", [], False
    )

    if not themes:
        await update.message.reply_text("Aucun thème disponible.")
        return ConversationHandler.END

    # Création des boutons pour les thèmes disponibles
    buttons = [[KeyboardButton(theme["name"])] for theme in themes]
    context.user_data["themes_mapping"] = {theme["name"]: theme["id"] for theme in themes}

    await update.message.reply_text(
        "Veuillez choisir un thème pour commencer le QCM :",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )
    return THEMES

# Sélectionner un thème
async def set_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    theme_name = update.message.text
    themes_mapping = context.user_data.get("themes_mapping", {})

    if theme_name not in themes_mapping:
        await update.message.reply_text("Thème invalide. Veuillez réessayer.")
        return THEMES

    context.user_data["selected_theme"] = themes_mapping[theme_name]
    await update.message.reply_text(f"Thème sélectionné : {theme_name}. Préparons le QCM.")
    return await ask_question(update, context)

# Poser une question
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.message.from_user.id
    selected_theme = context.user_data.get("selected_theme")

    user = await execute_query("SELECT * FROM users WHERE telegram_id = $1", (telegram_id,), fetchone=True)
    if not user:
        await update.message.reply_text("Erreur : Impossible de récupérer vos données. Veuillez réessayer.")
        return ConversationHandler.END

    current_question = user["current_question"]
    total_questions = await execute_query(
        "SELECT COUNT(*) as total FROM questions WHERE theme_id = $1",
        (selected_theme,), fetchone=True
    )

    if current_question >= total_questions["total"]:
        return await end_quiz(update, context)

    question = await execute_query(
        "SELECT * FROM questions WHERE theme_id = $1 LIMIT 1 OFFSET $2 ",
        (selected_theme, current_question), fetchone=True
    )
    if not question:
        return await end_quiz(update, context)

    reply_markup = ReplyKeyboardMarkup(
        [
            [KeyboardButton(question["option1"])],
            [KeyboardButton(question["option2"])],
            [KeyboardButton(question["option3"])],
            [KeyboardButton(question["option4"])],
        ],
        one_time_keyboard=True
    )
    await update.message.reply_text(question["question"], reply_markup=reply_markup)
    return QUESTION

# Vérifier la réponse
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_answer = update.message.text
    if user_answer == "Quitter":
        await update.message.reply_text("Merci d'avoir utilisé le QCM. À bientôt !")
        return ConversationHandler.END  # Quitte la conversation

    if user_answer == "Recommencer le QCM":
        # Réinitialiser les données de l'utilisateur dans la base de données
        telegram_id = update.message.from_user.id
        await execute_query(
            "UPDATE users SET score = 0, current_question = 0 WHERE telegram_id = $1",
            (telegram_id,)
        )

        # Relancer le quiz
        await update.message.reply_text("Le QCM recommence !")
        return await ask_question(update, context)  # Relance la première question

    selected_theme = context.user_data.get("selected_theme")
    telegram_id = update.message.from_user.id
    user = await execute_query("SELECT * FROM users WHERE telegram_id = $1", (telegram_id,), fetchone=True)
    current_question = user["current_question"]
    question = await execute_query(
        "SELECT * FROM questions WHERE theme_id = $1 OFFSET $2 LIMIT 1",
        (selected_theme, current_question), fetchone=True)

    if question and user_answer == question["correct_option"]:
        await execute_query("UPDATE users SET score = score + 1 WHERE telegram_id = $1", (telegram_id,))

    await execute_query("UPDATE users SET current_question = current_question + 1 WHERE telegram_id = $1", (telegram_id,))
    return await ask_question(update, context)

# Fin du QCM
async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.message.from_user.id

    user = await execute_query("SELECT * FROM users WHERE telegram_id = $1", (telegram_id,), fetchone=True)
    if not user:
        await update.message.reply_text("Erreur : Impossible de récupérer vos données. Veuillez réessayer.")
        return ConversationHandler.END

    score = user["score"]
    total_questions = user["current_question"]
    name = user["name"]

    await execute_query(
        "INSERT INTO scores_history (telegram_id, score, total_questions) VALUES ($1, $2, $3)",
        (telegram_id, score, total_questions)
    )

    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("Recommencer le QCM")], [KeyboardButton("Quitter")]],
        one_time_keyboard=True
    )

    await update.message.reply_text(
        f"Félicitations {name} ! Vous avez terminé le QCM.\n"
        f"Votre score final est : {score}/{total_questions}.\n"
        "Voulez-vous recommencer ou quitter ?"
        "Tapez /start pour recommencer ou /historique pour voir vos scores passés.",
        reply_markup=reply_markup
    )
    return QUESTION

# Historique des scores
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.message.from_user.id

    history = await execute_query(
        "SELECT score, total_questions, attempt_date FROM scores_history WHERE telegram_id = $1 ORDER BY attempt_date DESC LIMIT 10",
        (telegram_id,)
    )

    if not history:
        await update.message.reply_text("Aucun score trouvé dans votre historique.")
        return

    message = "Voici votre historique de scores :\n\n"
    for entry in history:
        message += f"- Score : {entry['score']}/{entry['total_questions']} le {entry['attempt_date']}\n"

    await update.message.reply_text(message)

async def show_progress_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.message.from_user.id

    history = await execute_query(
        "SELECT score, total_questions, attempt_date FROM scores_history WHERE telegram_id = $1 ORDER BY attempt_date ASC",
        (telegram_id,)
    )

    if not history:
        await update.message.reply_text("Aucun score trouvé pour générer le graphique.")
        return

    scores = [entry["score"] for entry in history]
    total_questions = [entry["total_questions"] for entry in history]
    attempt_dates = [entry["attempt_date"] for entry in history]

    # Création du graphique
    fig, ax = plt.subplots()
    ax.plot(attempt_dates, scores, label="Score", marker="o")
    ax.plot(attempt_dates, total_questions, label="Total des questions", linestyle="--")
    ax.set_xlabel("Date de tentative")
    ax.set_ylabel("Score")
    ax.set_title("Progression des scores")
    ax.legend()

    # Conversion du graphique en image
    buf = io.BytesIO()
    plt.savefig(buf, format="PNG")
    buf.seek(0)

    await update.message.reply_photo(photo=buf)
    buf.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("QCM annulé. Merci d'avoir participé ! À bientôt.")
    return ConversationHandler.END

# Lancer l'application

# Lancer l'application Telegram
def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register)],
            THEMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_theme)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],  # Commande pour annuler
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("historique", show_history))
    application.add_handler(CommandHandler("progression", show_progress_chart))

    # Lancer le bot Telegram dans un thread séparé
    threading.Thread(target=application.run_polling).start()

if __name__ == "__main__":
    # Lancer le serveur Flask
    threading.Thread(target=run_flask).start()

    # Lancer l'application principale
    main()
