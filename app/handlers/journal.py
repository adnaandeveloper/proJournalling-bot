from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.db.database import SessionLocal
from app.db.models import Trade, User, Account, Pair
from datetime import datetime, timedelta
from sqlalchemy import func
PAGE_SIZE=10
async def show(update,context):
    q=update.callback_query; await q.answer()
    _,flt,page=q.data.split(":"); page=int(page)
    db=SessionLocal(); u=db.query(User).filter_by(telegram_id=q.from_user.id).first()
    qry=db.query(Trade).filter_by(user_id=u.id)
    now=datetime.utcnow()
    if flt=="day": qry=qry.filter(Trade.created_at>=now.replace(hour=0,minute=0,second=0))
    elif flt=="week": qry=qry.filter(Trade.created_at>=now-timedelta(days=7))
    elif flt=="month": qry=qry.filter(func.date_trunc('month',Trade.created_at)==func.date_trunc('month',now))
    total=qry.count(); trades=qry.order_by(Trade.id.desc()).offset(page*PAGE_SIZE).limit(PAGE_SIZE).all()
    wins=qry.filter(Trade.result=="win").count(); losses=qry.filter(Trade.result.in_(["loss","sl"])).count()
    pl_sum=db.query(func.coalesce(func.sum(Trade.actual_pl),0)).filter(Trade.user_id==u.id)
    if flt!="all":
        if flt=="day": pl_sum=pl_sum.filter(Trade.created_at>=now.replace(hour=0,minute=0))
        elif flt=="week": pl_sum=pl_sum.filter(Trade.created_at>=now-timedelta(days=7))
        elif flt=="month": pl_sum=pl_sum.filter(func.date_trunc('month',Trade.created_at)==func.date_trunc('month',now))
    pl=pl_sum.scalar()
    txt=f"Filter: {flt} | Trades: {total} | Wins: {wins} | Loss: {losses} | P/L: ${pl:.2f}\n\n"
    kb=[]
    for t in trades:
        kb.append([InlineKeyboardButton(f"#{t.id} {t.direction} ${t.actual_pl or 0}",callback_data=f"view:{t.id}")])
    nav=[]
    if page>0: nav.append(InlineKeyboardButton("⬅️",callback_data=f"journal:{flt}:{page-1}"))
    if (page+1)*PAGE_SIZE<total: nav.append(InlineKeyboardButton("➡️",callback_data=f"journal:{flt}:{page+1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton("Dag",callback_data="journal:day:0"),InlineKeyboardButton("Uge",callback_data="journal:week:0"),InlineKeyboardButton("Måned",callback_data="journal:month:0"),InlineKeyboardButton("Alt",callback_data="journal:all:0")])
    await q.edit_message_text(txt,reply_markup=InlineKeyboardMarkup(kb)); db.close()
async def view(update,context):
    q=update.callback_query; await q.answer(); tid=int(q.data.split(":")[1])
    db=SessionLocal(); t=db.query(Trade).get(tid); acc=db.query(Account).get(t.account_id); pair=db.query(Pair).get(t.pair_id)
    cap=f"#{t.id} {pair.symbol} {t.direction.upper()}\nKonto: {acc.name}\nTarget: ${t.target_profit} Risk: ${t.risk}\nStatus: {t.status} Result: {t.result or '-'} P/L: ${t.actual_pl or 0}\nOprettet: {t.created_at.strftime('%Y-%m-%d %H:%M')}"
    await context.bot.send_photo(chat_id=q.from_user.id,photo=t.setup_file_id,caption=cap)
    if t.close_file_id: await context.bot.send_photo(chat_id=q.from_user.id,photo=t.close_file_id,caption="Exit")
    db.close()
