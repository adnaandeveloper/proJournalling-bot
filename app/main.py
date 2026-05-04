from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from app.config import BOT_TOKEN
from app.db.database import init_db
from app.handlers import start, trade_new, trade_close, accounts, pairs, journal, cashflow, stats, admin
import os

def main():
    # --- DEBUG: se hvad Railway sender ---
    print("=== TOKEN CHECK ===")
    print("BOT_TOKEN sat?", bool(BOT_TOKEN))
    print("Længde:", len(BOT_TOKEN) if BOT_TOKEN else 0)
    print("Starter med:", BOT_TOKEN[:6] + "..." if BOT_TOKEN else "INGEN")
    print("===================")
    
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        raise RuntimeError("STOP: BOT_TOKEN mangler i Railway Variables. Gå til Variables → tilføj BOT_TOKEN")

    init_db()
    app=ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start.start))
    app.add_handler(CommandHandler("adduser",admin.adduser))
    app.add_handler(CommandHandler("addpair",pairs.addpair))
    new_conv=ConversationHandler(entry_points=[CallbackQueryHandler(trade_new.start,pattern="^new_trade$")],states={trade_new.DIR:[CallbackQueryHandler(trade_new.dir_chosen)],trade_new.ACC:[CallbackQueryHandler(trade_new.acc_chosen)],trade_new.PAIR:[CallbackQueryHandler(trade_new.pair_chosen)],trade_new.PHOTO:[MessageHandler(filters.PHOTO,trade_new.photo)],trade_new.TARGET:[MessageHandler(filters.TEXT&~filters.COMMAND,trade_new.target)],trade_new.RISK:[MessageHandler(filters.TEXT&~filters.COMMAND,trade_new.risk)],trade_new.COMMENT:[MessageHandler(filters.TEXT&~filters.COMMAND,trade_new.comment)]},fallbacks=[])
    close_conv=ConversationHandler(entry_points=[CallbackQueryHandler(trade_close.start,pattern="^close_trade$")],states={trade_close.SEL:[CallbackQueryHandler(trade_close.sel)],trade_close.RES:[CallbackQueryHandler(trade_close.res)],trade_close.PL:[MessageHandler(filters.TEXT&~filters.COMMAND,trade_close.pl)],trade_close.PHOTO:[MessageHandler(filters.PHOTO|filters.COMMAND,trade_close.photo)],trade_close.COMM:[MessageHandler(filters.TEXT&~filters.COMMAND,trade_close.comm)]},fallbacks=[])
    acc_conv=ConversationHandler(entry_points=[CallbackQueryHandler(accounts.create_start,pattern="^acc_create$")],states={accounts.TYPE:[CallbackQueryHandler(accounts.type_chosen)],accounts.NAME:[MessageHandler(filters.TEXT&~filters.COMMAND,accounts.name_given)]},fallbacks=[])
    cf_conv=ConversationHandler(entry_points=[CallbackQueryHandler(cashflow.start,pattern="^cashflow$")],states={cashflow.TYPE:[CallbackQueryHandler(cashflow.type_chosen)],cashflow.ACC:[CallbackQueryHandler(cashflow.acc_chosen)],cashflow.AMT:[MessageHandler(filters.TEXT&~filters.COMMAND,cashflow.amt)],cashflow.NOTE:[MessageHandler(filters.TEXT&~filters.COMMAND,cashflow.note)]},fallbacks=[])
    app.add_handler(new_conv); app.add_handler(close_conv); app.add_handler(acc_conv); app.add_handler(cf_conv)
    app.add_handler(CallbackQueryHandler(accounts.menu,pattern="^accounts$"))
    app.add_handler(CallbackQueryHandler(pairs.menu,pattern="^pairs$"))
    app.add_handler(CallbackQueryHandler(journal.show,pattern="^journal:"))
    app.add_handler(CallbackQueryHandler(journal.view,pattern="^view:"))
    app.add_handler(CallbackQueryHandler(stats.show,pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(start.back_menu,pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: admin.menu(u,c),pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: start.back_menu(u,c),pattern="^lang$"))
    app.run_polling()

if __name__=="__main__": main()