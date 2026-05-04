from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Account, User, Trade, Cashflow
from sqlalchemy import func

TYPE, NAME, BAL, EDIT = range(4)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = SessionLocal()
    u = db.query(User).filter_by(telegram_id=q.from_user.id).first()
    accs = db.query(Account).filter_by(user_id=u.id).all()

    lines = []
    kb = []
    for a in accs:
        trades_pl = db.query(func.coalesce(func.sum(Trade.actual_pl), 0)).filter(
            Trade.account_id == a.id, Trade.status == 'closed').scalar() or 0
        cash_pl = db.query(func.coalesce(func.sum(Cashflow.amount), 0)).filter(
            Cashflow.account_id == a.id).scalar() or 0
        bal = (a.start_balance or 0) + trades_pl + cash_pl
        status_emoji = "🟢" if a.status=="active" else "✅" if a.status=="passed" else "💥" if a.status=="blown" else "⏸️"
        lines.append(f"{status_emoji} {a.name} ({a.type}) | ${bal:.2f}")
        kb.append([
            InlineKeyboardButton("✏️", callback_data=f"accedit:{a.id}"),
            InlineKeyboardButton("⚙️", callback_data=f"accstat:{a.id}"),
            InlineKeyboardButton("🗑️", callback_data=f"accdel:{a.id}")
        ])

    text = "Dine konti:\n" + "\n".join(lines) if lines else "Ingen konti endnu"
    kb.append([InlineKeyboardButton("➕ Opret konto", callback_data="acc_create")])
    kb.append([InlineKeyboardButton("⬅️ Tilbage", callback_data="menu")])
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    db.close()

async def create_start(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data.clear() # vigtig: rydder gammel samtale
    kb = [[InlineKeyboardButton("Challenge", callback_data="challenge")],
          [InlineKeyboardButton("Funded", callback_data="funded")],
          [InlineKeyboardButton("Live", callback_data="live")]]
    await q.edit_message_text("Vælg type:", reply_markup=InlineKeyboardMarkup(kb))
    return TYPE

async def type_chosen(update, context):
    context.user_data["atype"] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Navn på konto (fx FTMO 100k):")
    return NAME

async def name_given(update, context):
    context.user_data["aname"] = update.message.text
    await update.message.reply_text("Start balance USD? Skriv 0 hvis du starter fra 0")
    return BAL

async def bal_given(update, context):
    try:
        bal = float(update.message.text.replace(",", "."))
    except:
        await update.message.reply_text("Skriv et tal, fx 100000")
        return BAL
    try:
        db = SessionLocal()
        u = db.query(User).filter_by(telegram_id=update.effective_user.id).first()
        acc = Account(user_id=u.id, name=context.user_data["aname"],
                      type=context.user_data["atype"], status="active", start_balance=bal)
        db.add(acc)
        db.commit()
        name = acc.name
        db.close()
        await update.message.reply_text(f"✅ Konto oprettet: {name} med ${bal:.2f}")
    except Exception as e:
        await update.message.reply_text(f"Fejl: {e}")
    context.user_data.clear()
    return ConversationHandler.END

async def edit_start(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["edit_id"] = int(q.data.split(":")[1])
    await q.edit_message_text("Ny start-balance USD?")
    return EDIT

async def edit_save(update, context):
    try:
        bal = float(update.message.text.replace(",", "."))
        db = SessionLocal()
        acc = db.query(Account).get(context.user_data["edit_id"])
        acc.start_balance = bal
        db.commit()
        db.close()
        await update.message.reply_text(f"Balance opdateret til ${bal:.2f}")
    except:
        await update.message.reply_text("Skriv et tal")
        return EDIT
    return ConversationHandler.END

async def status_menu(update, context):
    q = update.callback_query
    await q.answer()
    acc_id = int(q.data.split(":")[1])
    kb = [
        [InlineKeyboardButton("🟢 Aktiv", callback_data=f"setstat:{acc_id}:active")],
        [InlineKeyboardButton("✅ Passed", callback_data=f"setstat:{acc_id}:passed")],
        [InlineKeyboardButton("💥 Blown", callback_data=f"setstat:{acc_id}:blown")],
        [InlineKeyboardButton("⏸️ Pauset", callback_data=f"setstat:{acc_id}:paused")],
        [InlineKeyboardButton("⬅️ Tilbage", callback_data="accounts")]
    ]
    await q.edit_message_text("Vælg ny status:", reply_markup=InlineKeyboardMarkup(kb))

async def status_set(update, context):
    q = update.callback_query
    await q.answer()
    _, acc_id, new_status = q.data.split(":")
    db = SessionLocal()
    acc = db.query(Account).get(int(acc_id))
    acc.status = new_status
    db.commit()
    db.close()
    await q.answer(f"Status sat til {new_status}")
    return await menu(update, context)

async def delete_start(update, context):
    q = update.callback_query
    await q.answer()
    acc_id = int(q.data.split(":")[1])
    kb = [[InlineKeyboardButton("Ja, slet", callback_data=f"accdelok:{acc_id}"),
           InlineKeyboardButton("Annuller", callback_data="accounts")]]
    await q.edit_message_text("Slet konto permanent?", reply_markup=InlineKeyboardMarkup(kb))

async def delete_ok(update, context):
    q = update.callback_query
    await q.answer()
    acc_id = int(q.data.split(":")[1])
    db = SessionLocal()
    db.query(Trade).filter_by(account_id=acc_id).delete()
    db.query(Cashflow).filter_by(account_id=acc_id).delete()
    db.query(Account).filter_by(id=acc_id).delete()
    db.commit()
    db.close()
    await q.edit_message_text("Konto slettet")