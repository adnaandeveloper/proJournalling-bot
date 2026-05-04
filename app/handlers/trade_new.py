from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.db.database import SessionLocal
from app.db.models import Trade, Account, Pair, User
from app.i18n import t
DIR,ACC,PAIR,PHOTO,TARGET,RISK,COMMENT=range(7)
async def start(update,context):
    q=update.callback_query; await q.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    kb=[[InlineKeyboardButton(t(u.language,"buy"),callback_data="buy")],[InlineKeyboardButton(t(u.language,"sell"),callback_data="sell")]]
    await q.edit_message_text(t(u.language,"choose_direction"),reply_markup=InlineKeyboardMarkup(kb)); db.close(); return DIR
async def dir_chosen(update,context):
    context.user_data["direction"]=update.callback_query.data; await update.callback_query.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    accs=db.query(Account).filter_by(user_id=u.id,status="active").all()
    if not accs: await update.callback_query.edit_message_text("Opret konto først under Konti"); db.close(); return ConversationHandler.END
    kb=[[InlineKeyboardButton(a.name,callback_data=str(a.id))] for a in accs]
    await update.callback_query.edit_message_text(t(u.language,"choose_account"),reply_markup=InlineKeyboardMarkup(kb)); db.close(); return ACC
async def acc_chosen(update,context):
    context.user_data["account_id"]=int(update.callback_query.data); await update.callback_query.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    pairs=db.query(Pair).filter_by(user_id=u.id).all()
    kb=[[InlineKeyboardButton(p.symbol,callback_data=str(p.id))] for p in pairs] if pairs else [[InlineKeyboardButton("Add pair first",callback_data="x")]]
    await update.callback_query.edit_message_text(t(u.language,"choose_pair"),reply_markup=InlineKeyboardMarkup(kb)); db.close(); return PAIR
async def pair_chosen(update,context):
    context.user_data["pair_id"]=int(update.callback_query.data); await update.callback_query.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    await update.callback_query.edit_message_text(t(u.language,"send_photo")); db.close(); return PHOTO
async def photo(update,context):
    context.user_data["setup"]=update.message.photo[-1].file_id
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    await update.message.reply_text(t(u.language,"enter_target")); db.close(); return TARGET
async def target(update,context):
    context.user_data["target"]=float(update.message.text.replace(",",".")); db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    await update.message.reply_text(t(u.language,"enter_risk")); db.close(); return RISK
async def risk(update,context):
    context.user_data["risk"]=float(update.message.text.replace(",",".")); db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    await update.message.reply_text(t(u.language,"enter_comment")); db.close(); return COMMENT
async def comment(update,context):
    com="" if update.message.text=="/skip" else update.message.text
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    tr=Trade(user_id=u.id,account_id=context.user_data["account_id"],pair_id=context.user_data["pair_id"],direction=context.user_data["direction"],target_profit=context.user_data["target"],risk=context.user_data["risk"],comment=com,setup_file_id=context.user_data["setup"],status="open")
    db.add(tr); db.commit(); await update.message.reply_text(t(u.language,"trade_saved",id=tr.id)); db.close(); return ConversationHandler.END
