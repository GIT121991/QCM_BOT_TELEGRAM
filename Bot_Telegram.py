import matplotlib.pyplot as plt
import io
import mysql.connector
from mysql.connector import Error
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in the environment variables.")

# États du bot
REGISTER, THEMES, QUESTION = range(3)

# Configuration MySQL
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "qcmbotdb"
}

# Fonction générique pour exécuter des requêtes SQL
def execute_query(query, params=None, fetchone=False):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        connection.commit()
        return result
    except Error as e:
        print(f"Erreur MySQL : {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Démarrage du bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bienvenue au QCM ! Veuillez entrer votre nom pour commencer.")
    return REGISTER

# Enregistrement de l'utilisateur
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    telegram_id = update.message.from_user.id

    execute_query(
        """
        INSERT INTO users (telegram_id, name)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE name = VALUES(name), score = 0, current_question = 0
        """,
        (telegram_id, name)
    )

    await update.message.reply_text(f"Merci {name} ! Préparons-nous pour le QCM.")
    return await choose_theme(update, context)

# Afficher les thèmes disponibles et permettre à l'utilisateur de choisir
async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    themes = execute_query("SELECT id, name FROM themes")
    if not themes:
        await update.message.reply_text("Aucun thème disponible.")
        return ConversationHandler.END

    buttons = [[KeyboardButton(theme["name"])] for theme in themes]
    context.user_data["themes_mapping"] = {theme["name"]: theme["id"] for theme in themes}

    await update.message.reply_text(
        "Veuillez choisir un thème pour commencer le QCM :",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )
    return THEMES

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

    user = execute_query("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,), fetchone=True)
    if not user:
        await update.message.reply_text("Erreur : Impossible de récupérer vos données. Veuillez réessayer.")
        return ConversationHandler.END

    current_question = user["current_question"]
    total_questions = execute_query("SELECT COUNT(*) as total FROM questions WHERE theme_id = %s",
                                    (selected_theme,), fetchone=True)["total"]

    if current_question >= total_questions:
        return await end_quiz(update, context)

    question = execute_query("SELECT * FROM questions WHERE theme_id = %s LIMIT %s, 1",
        (selected_theme, current_question),
        fetchone=True
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
        execute_query("UPDATE users SET score = 0, current_question = 0 WHERE telegram_id = %s", (telegram_id,))

        # Relancer le quiz
        await update.message.reply_text("Le QCM recommence !")
        return await ask_question(update, context)  # Relance la première question

    selected_theme = context.user_data.get("selected_theme")
    telegram_id = update.message.from_user.id
    user = execute_query("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,), fetchone=True)
    current_question = user["current_question"]

    question = execute_query("SELECT * FROM questions WHERE theme_id = %s LIMIT %s, 1",
                             (selected_theme, current_question), fetchone=True)

    if question and user_answer == question["correct_option"]:
        execute_query("UPDATE users SET score = score + 1 WHERE telegram_id = %s", (telegram_id,))

    execute_query("UPDATE users SET current_question = current_question + 1 WHERE telegram_id = %s", (telegram_id,))
    return await ask_question(update, context)

# Fin du QCM
async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.message.from_user.id

    user = execute_query("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,), fetchone=True)
    if not user:
        await update.message.reply_text("Erreur : Impossible de récupérer vos données. Veuillez réessayer.")
        return ConversationHandler.END

    score = user["score"]
    total_questions = user["current_question"]
    name = user["name"]

    execute_query(
        """
        INSERT INTO scores_history (telegram_id, score, total_questions)
        VALUES (%s, %s, %s)
        """,
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
        reply_markup = reply_markup
    )
    return QUESTION

# Historique des scores
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.message.from_user.id

    history = execute_query(
        """
        SELECT score, total_questions, attempt_date
        FROM scores_history
        WHERE telegram_id = %s
        ORDER BY attempt_date DESC
        LIMIT 10
        """,
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

    history = execute_query(
        """
        SELECT score, total_questions, attempt_date
        FROM scores_history
        WHERE telegram_id = %s
        ORDER BY attempt_date ASC
        """,
        (telegram_id,)
    )

    if not history:
        await update.message.reply_text("Aucun score trouvé dans votre historique.")
        return

    # Préparation des données pour le graphique
    dates = [entry["attempt_date"] for entry in history]
    scores = [entry["score"] for entry in history]
    max_scores = [entry["total_questions"] for entry in history]

    # Création du graphique
    plt.figure(figsize=(10, 6))
    plt.plot(dates, scores, label="Score", marker="o")
    plt.plot(dates, max_scores, label="Score Maximum", linestyle="--")
    plt.title("Progression des scores")
    plt.xlabel("Date")
    plt.ylabel("Score")
    plt.legend()
    plt.grid()

    # Sauvegarde dans un fichier temporaire
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()

    # Envoi du graphique via Telegram
    await update.message.reply_photo(photo=buffer)
    buffer.close()

# Annulation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("QCM annulé. Merci d'avoir participé ! À bientôt.")
    return ConversationHandler.END


# Main
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER: [MessageHandler(filters.TEXT, register)],
            THEMES: [MessageHandler(filters.TEXT, set_theme)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],  # Commande pour annuler
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("historique", show_history))
    application.add_handler(CommandHandler("progression", show_progress_chart))
    application.run_polling()

if __name__ == "__main__":
    main()
