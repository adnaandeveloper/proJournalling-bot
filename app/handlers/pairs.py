from telegram import Update
from telegram.ext import ContextTypes
from app.db.database import SessionLocal
from app.db.models import Pair, User
async def menu(update,context):
    q=update.callback_query; await q.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    pairs=db.query(Pair).filter_by(user_id=u.id).all()
    txt="Pairs:\n"+ "\n".join(p.symbol for p in pairs) if pairs else "Ingen. Send /addpair EURUSD"
    await q.edit_message_text(txt); db.close()
async def addpair(update,context):
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    sym=context.args[0].upper(); db.add(Pair(user_id=u.id,symbol=sym)); db.commit()
    await update.message.reply_text(f"Pair {sym} tilføjet"); db.close()
