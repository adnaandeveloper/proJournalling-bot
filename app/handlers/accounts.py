from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Account, User, Trade, Cashflow
from sqlalchemy import func

TYPE, NAME, BAL = range(3)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = SessionLocal()
    u = db.query(User).filter_by(telegram_id=q.from_user.id).first()
    accs = db.query(Account).filter_by(user_id=u.id).all()

    lines = []
    for a in accs:
        trades_pl = db.query(func.coalesce(func.sum(Trade.actual_pl), 0)).filter(
            Trade.account_id == a.id, Trade.status == 'closed'
        ).scalar() or 0
        cash_pl = db.query(func.coalesce(func.sum(Cashflow.amount), 0)).filter(
            Cashflow.account_id == a.id
        ).scalar() or 0
        balance = (a.start_balance or 0) + trades_pl + cash_pl
        lines.append(f"{a.name} ({a.type}) - {a.status} | Balance: ${balance:.2f}")

    text = "Dine konti:\n" + "\n".join(lines) if lines else "Ingen konti endnu"
    kb = [
        [InlineKeyboardButton("➕ Opret konto", callback_data="acc_create")],
        [InlineKeyboardButton("⬅️ Tilbage", callback_data="menu")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    db.close()

async def create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    kb = [
        [InlineKeyboardButton("Challenge", callback_data="challenge")],
        [InlineKeyboardButton("Funded", callback_data="funded")],
        [InlineKeyboardButton("Live", callback_data="live")]
    ]
    await q.edit_message_text("Vælg type:", reply_markup=InlineKeyboardMarkup(kb))
    return TYPE

async def type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["atype"] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Skriv navn på konto (fx FTMO 100k):")
    return NAME

async def name_given(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["aname"] = update.message.text
    await update.message.reply_text("Start balance i USD? (skriv 0 hvis du starter fra 0)")
    return BAL

async def bal_given(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bal = float(update.message.text.replace(",", "."))
    except:
        await update.message.reply_text("Skriv et tal, fx 0 eller 100000")
        return BAL

    db = SessionLocal()
    u = db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    acc = Account(
        user_id=u.id,
        name=context.user_data["aname"],
        type=context.user_data["atype"],
        status="active",
        start_balance=bal
    )
    db.add(acc)
    db.commit()
    db.close()

    await update.message.reply_text(f"Konto oprettet: {context.user_data['aname']} med start ${bal:.2f}")
    return ConversationHandler.END