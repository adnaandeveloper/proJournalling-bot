from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Account, User, Cashflow

TYPE, ACC, AMT, NOTE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("➕ Deposit", callback_data="deposit")],
        [InlineKeyboardButton("➖ Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("⬅️ Tilbage", callback_data="menu")]
    ]
    await q.edit_message_text("Vælg type:", reply_markup=InlineKeyboardMarkup(kb))
    return TYPE

async def type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["cf_type"] = q.data
    db = SessionLocal()
    u = db.query(User).filter_by(telegram_id=q.from_user.id).first()
    accs = db.query(Account).filter_by(user_id=u.id).all()
    db.close()
    
    kb = []
    for a in accs:
        emoji = "🟢" if a.status=="active" else "✅" if a.status=="passed" else "💥" if a.status=="blown" else "⏸️"
        kb.append([InlineKeyboardButton(f"{emoji} {a.name} ({a.type})", callback_data=str(a.id))])
    kb.append([InlineKeyboardButton("⬅️ Tilbage", callback_data="menu")])
    
    await q.edit_message_text("Vælg konto:", reply_markup=InlineKeyboardMarkup(kb))
    return ACC

async def acc_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["cf_acc"] = int(q.data)
    await q.edit_message_text("Beløb USD? (skriv tal)")
    return AMT

async def amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = float(update.message.text.replace(",", "."))
    except:
        await update.message.reply_text("Skriv et tal")
        return AMT
    context.user_data["cf_amt"] = amt if context.user_data["cf_type"]=="deposit" else -abs(amt)
    await update.message.reply_text("Note? (eller skriv -)")
    return NOTE

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text if update.message.text != "-" else ""
    db = SessionLocal()
    cf = Cashflow(
        account_id=context.user_data["cf_acc"],
        amount=context.user_data["cf_amt"],
        note=note,
        type=context.user_data["cf_type"]
    )
    db.add(cf)
    db.commit()
    db.close()
    await update.message.reply_text(f"✅ Cashflow registreret: ${context.user_data['cf_amt']:.2f}")
    context.user_data.clear()
    return ConversationHandler.END