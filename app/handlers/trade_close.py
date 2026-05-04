from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Trade, User
from app.i18n import t
from datetime import datetime
SEL,RES,PL,PHOTO,COMM=range(5)
async def start(update,context):
    q=update.callback_query; await q.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    trades=db.query(Trade).filter_by(user_id=u.id,status="open").order_by(Trade.id.desc()).limit(20).all()
    if not trades: await q.edit_message_text(t(u.language,"no_open")); db.close(); return ConversationHandler.END
    kb=[[InlineKeyboardButton(f"#{t.id} {t.direction.upper()}",callback_data=str(t.id))] for t in trades]
    await q.edit_message_text("Vælg trade:",reply_markup=InlineKeyboardMarkup(kb)); db.close(); return SEL
async def sel(update,context):
    context.user_data["tid"]=int(update.callback_query.data); await update.callback_query.answer()
    kb=[[InlineKeyboardButton("WIN",callback_data="win"),InlineKeyboardButton("LOSS",callback_data="loss")],[InlineKeyboardButton("BE",callback_data="be"),InlineKeyboardButton("SL",callback_data="sl")]]
    await update.callback_query.edit_message_text("Resultat?",reply_markup=InlineKeyboardMarkup(kb)); return RES
async def res(update,context):
    context.user_data["res"]=update.callback_query.data; await update.callback_query.answer()
    await update.callback_query.edit_message_text("Faktisk P/L i USD?"); return PL
async def pl(update,context):
    context.user_data["pl"]=float(update.message.text.replace(",",".")); await update.message.reply_text("Send exit screenshot eller /skip"); return PHOTO
async def photo(update,context):
    context.user_data["close"]=update.message.photo[-1].file_id if update.message.photo else None
    await update.message.reply_text("Kommentar eller /skip"); return COMM
async def comm(update,context):
    com="" if update.message.text=="/skip" else update.message.text
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    tr=db.query(Trade).get(context.user_data["tid"]); tr.status="closed"; tr.result=context.user_data["res"]; tr.actual_pl=context.user_data["pl"]; tr.close_file_id=context.user_data["close"]; tr.close_comment=com; tr.closed_at=datetime.utcnow()
    db.commit(); await update.message.reply_text(t(u.language,"trade_closed")); db.close(); return ConversationHandler.END
