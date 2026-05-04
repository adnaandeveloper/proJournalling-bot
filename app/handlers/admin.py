from telegram import Update
from telegram.ext import ContextTypes
from app.db.database import SessionLocal
from app.db.models import User
from app.config import ADMIN_ID
async def adduser(update,context):
    if update.effective_user.id!=ADMIN_ID: return
    tid=int(context.args[0]); db=SessionLocal(); u=db.query(User).filter_by(telegram_id=tid).first()
    if not u: u=User(telegram_id=tid,is_active=1); db.add(u)
    else: u.is_active=1
    db.commit(); await update.message.reply_text(f"Bruger {tid} aktiveret"); db.close()
async def menu(update,context):
    q=update.callback_query; await q.answer(); await q.edit_message_text("Admin: /adduser <telegram_id>")
