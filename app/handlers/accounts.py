from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Account, User
TYPE,NAME=range(2)
async def menu(update,context):
    q=update.callback_query; await q.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    accs=db.query(Account).filter_by(user_id=u.id).all()
    text="Dine konti:\n" + "\n".join([f"{a.id}. {a.name} ({a.type}) - {a.status}" for a in accs]) if accs else "Ingen konti endnu"
    kb=[[InlineKeyboardButton("➕ Opret konto",callback_data="acc_create")],[InlineKeyboardButton("⬅️ Tilbage",callback_data="menu")]]
    await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup(kb)); db.close()
async def create_start(update,context):
    q=update.callback_query; await q.answer()
    kb=[[InlineKeyboardButton("Challenge",callback_data="challenge")],[InlineKeyboardButton("Funded",callback_data="funded")],[InlineKeyboardButton("Live",callback_data="live")]]
    await q.edit_message_text("Vælg type:",reply_markup=InlineKeyboardMarkup(kb)); return TYPE
async def type_chosen(update,context):
    context.user_data["atype"]=update.callback_query.data; await update.callback_query.answer()
    await update.callback_query.edit_message_text("Skriv navn på konto (fx FTMO 100k):"); return NAME
async def name_given(update,context):
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    acc=Account(user_id=u.id,name=update.message.text,type=context.user_data["atype"],status="active")
    db.add(acc); db.commit(); await update.message.reply_text(f"Konto oprettet: {acc.name}"); db.close()
    return ConversationHandler.END
