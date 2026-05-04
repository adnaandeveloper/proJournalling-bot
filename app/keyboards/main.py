from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.i18n import t
def main_menu(lang,is_admin=False):
    rows=[
        [InlineKeyboardButton(t(lang,"new_trade"),callback_data="new_trade")],
        [InlineKeyboardButton(t(lang,"close_trade"),callback_data="close_trade")],
        [InlineKeyboardButton(t(lang,"journal"),callback_data="journal:all:0"), InlineKeyboardButton(t(lang,"stats"),callback_data="stats")],
        [InlineKeyboardButton(t(lang,"accounts"),callback_data="accounts"), InlineKeyboardButton(t(lang,"pairs"),callback_data="pairs")],
        [InlineKeyboardButton(t(lang,"cashflow"),callback_data="cashflow"), InlineKeyboardButton(t(lang,"language"),callback_data="lang")],
    ]
    if is_admin: rows.append([InlineKeyboardButton(t(lang,"admin"),callback_data="admin")])
    return InlineKeyboardMarkup(rows)
