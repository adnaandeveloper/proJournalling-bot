from telegram import Update
from telegram.ext import ContextTypes
from app.db.database import SessionLocal
from app.db.models import User
from app.keyboards.main import main_menu
from app.i18n import t
from app.config import ADMIN_ID
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=SessionLocal(); tg=update.effective_user.id
    user=db.query(User).filter_by(telegram_id=tg).first()
    if not user:
        user=User(telegram_id=tg,is_active=1 if tg==ADMIN_ID else 0); db.add(user); db.commit()
    if not user.is_active and tg!=ADMIN_ID:
        await update.message.reply_text("Adgang ikke godkendt. Kontakt admin."); db.close(); return
    await update.message.reply_text(t(user.language,"welcome"),reply_markup=main_menu(user.language,tg==ADMIN_ID)); db.close()
async def back_menu(update,context):
    q=update.callback_query; await q.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    await q.edit_message_text(t(u.language,"main_menu"),reply_markup=main_menu(u.language,q.from_user.id==ADMIN_ID)); db.close()
