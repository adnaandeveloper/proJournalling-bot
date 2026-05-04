import warnings
from telegram.warnings import PTBUserWarning
warnings.filterwarnings("ignore", category=PTBUserWarning)

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from app.config import BOT_TOKEN
from app.db.database import init_db
from app.handlers import start, trade_new, trade_close, accounts, pairs, journal, cashflow, stats, admin

def main():
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN mangler i Railway Variables")

    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("adduser", admin.adduser))
    app.add_handler(CommandHandler("addpair", pairs.addpair))

    new_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(trade_new.start, pattern="^new_trade$")],
        states={
            trade_new.DIR: [CallbackQueryHandler(trade_new.dir_chosen)],
            trade_new.ACC: [CallbackQueryHandler(trade_new.acc_chosen)],
            trade_new.PAIR: [CallbackQueryHandler(trade_new.pair_chosen)],
            trade_new.PHOTO: [MessageHandler(filters.PHOTO, trade_new.photo)],
            trade_new.TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_new.target)],
            trade_new.RISK: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_new.risk)],
            trade_new.COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_new.comment)]
        },
        fallbacks=[CommandHandler("cancel", start.back_menu), CallbackQueryHandler(start.back_menu, pattern="^menu$")],
        per_user=True, per_chat=True, per_message=False
    )

    close_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(trade_close.start, pattern="^close_trade$")],
        states={
            trade_close.SEL: [CallbackQueryHandler(trade_close.sel)],
            trade_close.RES: [CallbackQueryHandler(trade_close.res)],
            trade_close.PL: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_close.pl)],
            trade_close.PHOTO: [MessageHandler(filters.PHOTO | filters.COMMAND, trade_close.photo)],
            trade_close.COMM: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_close.comm)]
        },
        fallbacks=[CommandHandler("cancel", start.back_menu), CallbackQueryHandler(start.back_menu, pattern="^menu$")],
        per_user=True, per_chat=True, per_message=False
    )

    acc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(accounts.create_start, pattern="^acc_create$")],
        states={
            accounts.TYPE: [CallbackQueryHandler(accounts.type_chosen)],
            accounts.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, accounts.name_given)],
            accounts.BAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, accounts.bal_given)]
        },
        fallbacks=[CommandHandler("cancel", start.back_menu), CallbackQueryHandler(start.back_menu, pattern="^menu$")],
        per_user=True, per_chat=True, per_message=False
    )

    cf_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cashflow.start, pattern="^cashflow$")],
        states={
            cashflow.TYPE: [CallbackQueryHandler(cashflow.type_chosen)],
            cashflow.ACC: [CallbackQueryHandler(cashflow.acc_chosen)],
            cashflow.AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashflow.amt)],
            cashflow.NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashflow.note)]
        },
        fallbacks=[CommandHandler("cancel", start.back_menu), CallbackQueryHandler(start.back_menu, pattern="^menu$")],
        per_user=True, per_chat=True, per_message=False
    )

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(accounts.edit_start, pattern="^accedit:")],
        states={
            accounts.EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, accounts.edit_save)]
        },
        fallbacks=[CommandHandler("cancel", start.back_menu), CallbackQueryHandler(start.back_menu, pattern="^menu$")],
        per_user=True, per_chat=True, per_message=False
    )

    app.add_handler(new_conv)
    app.add_handler(close_conv)
    app.add_handler(acc_conv)
    app.add_handler(cf_conv)
    app.add_handler(edit_conv)

    app.add_handler(CallbackQueryHandler(accounts.menu, pattern="^accounts$"))
    app.add_handler(CallbackQueryHandler(accounts.delete_start, pattern="^accdel:"))
    app.add_handler(CallbackQueryHandler(accounts.delete_ok, pattern="^accdelok:"))
    app.add_handler(CallbackQueryHandler(accounts.status_menu, pattern="^accstat:"))
    app.add_handler(CallbackQueryHandler(accounts.status_set, pattern="^setstat:"))
    
    app.add_handler(CallbackQueryHandler(pairs.menu, pattern="^pairs$"))
    app.add_handler(CallbackQueryHandler(journal.show, pattern="^journal:"))
    app.add_handler(CallbackQueryHandler(journal.view, pattern="^view:"))

    async def stats_temp(update, context):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("📊 Stats kommer snart")
    app.add_handler(CallbackQueryHandler(stats_temp, pattern="^stats$"))

    app.add_handler(CallbackQueryHandler(start.back_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: admin.menu(u, c), pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: start.back_menu(u, c), pattern="^lang$"))

    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()