from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Cashflow, Account, User
TYPE,ACC,AMT,NOTE=range(4)

async def start(update,context):
    q=update.callback_query; await q.answer()
    # reset any old data
    context.user_data.clear()
    kb=[[InlineKeyboardButton("Payout",callback_data="payout")],
        [InlineKeyboardButton("Challenge fee",callback_data="challenge_fee")],
        [InlineKeyboardButton("Deposit",callback_data="deposit")]]
    await q.edit_message_text("Vælg type:",reply_markup=InlineKeyboardMarkup(kb))
    return TYPE

async def type_chosen(update,context):
    context.user_data["ctype"]=update.callback_query.data
    await update.callback_query.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    accs=db.query(Account).filter_by(user_id=u.id).all(); db.close()
    if not accs:
        await update.callback_query.edit_message_text("Du har ingen konti endnu. Opret en under 💼 Konti først.")
        return ConversationHandler.END
    kb=[[InlineKeyboardButton(a.name,callback_data=str(a.id))] for a in accs]
    await update.callback_query.edit_message_text("Vælg konto:",reply_markup=InlineKeyboardMarkup(kb))
    return ACC

async def acc_chosen(update,context):
    data = update.callback_query.data
    await update.callback_query.answer()
    # guard: hvis brugeren klikker en anden knap mens vi venter
    if not data.isdigit():
        await update.callback_query.edit_message_text("Afbrudt. Start forfra fra menuen.")
        return ConversationHandler.END
    context.user_data["aid"]=int(data)
    await update.callback_query.edit_message_text("Beløb i USD?")
    return AMT

async def amt(update,context):
    try:
        context.user_data["amt"]=float(update.message.text.replace(",","."))
    except:
        await update.message.reply_text("Skriv et tal, fx 150")
        return AMT
    await update.message.reply_text("Note eller /skip")
    return NOTE

async def note(update,context):
    n="" if update.message.text=="/skip" else update.message.text
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    amt=context.user_data["amt"]; typ=context.user_data["ctype"]
    if typ!="payout": amt=-abs(amt)
    cf=Cashflow(user_id=u.id,account_id=context.user_data["aid"],type=typ,amount=amt,note=n)
    db.add(cf); db.commit(); db.close()
    await update.message.reply_text(f"Cashflow gemt: {typ} ${context.user_data['amt']}")
    return ConversationHandler.END

async def cancel(update,context):
    await update.message.reply_text("Annulleret")
    return ConversationHandler.END
