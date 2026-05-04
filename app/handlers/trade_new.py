from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Trade, Account, Pair, User
from app.i18n import t

DIR, ACC, PAIR, PHOTO, TARGET, RISK, COMMENT = range(7)

async def start(update, context):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton("BUY", callback_data="buy")],
          [InlineKeyboardButton("SELL", callback_data="sell")]]
    await q.edit_message_text("Vælg retning:", reply_markup=InlineKeyboardMarkup(kb))
    return DIR

async def dir_chosen(update, context):
    context.user_data["direction"] = update.callback_query.data
    context.user_data["selected_accs"] = set()
    await update.callback_query.answer()
    return await show_accounts(update, context)

async def show_accounts(update, context):
    q = update.callback_query
    db = SessionLocal()
    u = db.query(User).filter_by(telegram_id=q.from_user.id).first()
    accs = db.query(Account).filter_by(user_id=u.id, status="active").all()
    db.close()
    kb = []
    for a in accs:
        mark = "✅" if a.id in context.user_data["selected_accs"] else "⬜"
        kb.append([InlineKeyboardButton(f"{mark} {a.name}", callback_data=f"tog:{a.id}")])
    kb.append([InlineKeyboardButton("Færdig", callback_data="done")])
    await q.edit_message_text("Vælg én eller flere konti:", reply_markup=InlineKeyboardMarkup(kb))
    return ACC

async def acc_chosen(update, context):
    data = update.callback_query.data
    await update.callback_query.answer()
    if data.startswith("tog:"):
        aid = int(data.split(":")[1])
        s = context.user_data["selected_accs"]
        s.remove(aid) if aid in s else s.add(aid)
        return await show_accounts(update, context)
    if data == "done":
        if not context.user_data["selected_accs"]:
            await update.callback_query.answer("Vælg mindst én", show_alert=True)
            return ACC
        context.user_data["account_ids"] = list(context.user_data["selected_accs"])
        db = SessionLocal()
        u = db.query(User).filter_by(telegram_id=update.effective_user.id).first()
        pairs = db.query(Pair).filter_by(user_id=u.id).all()
        db.close()
        kb = [[InlineKeyboardButton(p.symbol, callback_data=str(p.id))] for p in pairs]
        await update.callback_query.edit_message_text("Vælg pair:", reply_markup=InlineKeyboardMarkup(kb))
        return PAIR

async def pair_chosen(update, context):
    context.user_data["pair_id"] = int(update.callback_query.data)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Send setup screenshot")
    return PHOTO

async def photo(update, context):
    context.user_data["setup"] = update.message.photo[-1].file_id
    await update.message.reply_text("Target profit USD?")
    return TARGET

async def target(update, context):
    context.user_data["target"] = float(update.message.text.replace(",", "."))
    await update.message.reply_text("Acceptabelt tab USD?")
    return RISK

async def risk(update, context):
    context.user_data["risk"] = float(update.message.text.replace(",", "."))
    await update.message.reply_text("Kommentar eller /skip")
    return COMMENT

async def comment(update, context):
    com = "" if update.message.text == "/skip" else update.message.text
    db = SessionLocal()
    u = db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    created = 0
    for aid in context.user_data["account_ids"]:
        tr = Trade(user_id=u.id, account_id=aid, pair_id=context.user_data["pair_id"],
                   direction=context.user_data["direction"],
                   target_profit=context.user_data["target"],
                   risk=context.user_data["risk"], comment=com,
                   setup_file_id=context.user_data["setup"], status="open")
        db.add(tr)
        created += 1
    db.commit()
    db.close()
    await update.message.reply_text(f"Trade oprettet på {created} konti ✅")
    return ConversationHandler.END