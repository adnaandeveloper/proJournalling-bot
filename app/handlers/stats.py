from telegram import Update
from telegram.ext import ContextTypes
from app.db.database import SessionLocal
from app.db.models import Trade, User
from datetime import datetime
import matplotlib.pyplot as plt
import io
from sqlalchemy import func
async def show(update,context):
    q=update.callback_query; await q.answer()
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    # group by month
    res=db.query(func.to_char(Trade.closed_at,'YYYY-MM'), func.sum(Trade.actual_pl)).filter(Trade.user_id==u.id, Trade.status=='closed').group_by(func.to_char(Trade.closed_at,'YYYY-MM')).order_by(func.to_char(Trade.closed_at,'YYYY-MM')).all()
    months=[r[0] for r in res]; pls=[float(r[1] or 0) for r in res]
    plt.figure(figsize=(8,4)); plt.bar(months,pls); plt.title("Månedlig P/L USD"); plt.xticks(rotation=45); plt.tight_layout()
    buf=io.BytesIO(); plt.savefig(buf,format='png'); buf.seek(0); plt.close()
    await context.bot.send_photo(chat_id=q.from_user.id, photo=buf, caption="Månedlig P/L"); db.close()
