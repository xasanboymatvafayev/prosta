"""
CASINO TELEGRAM BOT
aiogram 3.x + PostgreSQL
"""

import asyncio
import logging
import secrets
import string
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Database (assume you have async SQLAlchemy setup)
# from database import async_session, User, DepositRequest, WithdrawalRequest

logging.basicConfig(level=logging.INFO)

# ========================
# CONFIGURATION
# ========================

BOT_TOKEN = "8446614160:AAHdYsv8Qd_-h02E7nx3_Ttbe-MvQPTUFAo"
WEBAPP_URL = "https://prostauzb.vercel.app"  # Your web app URL
CHANNEL_ID = "@your_channel"  # Required subscription channel
ADMIN_IDS = [6365371142]  # Admin Telegram IDs

# ========================
# BOT SETUP
# ========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# ========================
# FSM STATES
# ========================

class DepositStates(StatesGroup):
    waiting_for_amount = State()

class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()


# ========================
# HELPER FUNCTIONS
# ========================

def generate_credentials():
    """Generate random login and password"""
    login = 'user_' + ''.join(secrets.choice(string.digits) for _ in range(8))
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    return login, password


async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to required channel"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎰 O'yinlar", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="👤 Profil", callback_data="profile"),
            InlineKeyboardButton(text="💰 Balans", callback_data="balance")
        ],
        [
            InlineKeyboardButton(text="➕ To'ldirish", callback_data="deposit"),
            InlineKeyboardButton(text="➖ Yechish", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="stats"),
            InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")
        ]
    ])
    return keyboard


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Subscription prompt keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")
        ],
        [
            InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")
        ]
    ])
    return keyboard


# ========================
# COMMAND HANDLERS
# ========================

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Check subscription first
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        await message.answer(
            "❌ <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
            f"📢 Kanal: {CHANNEL_ID}\n\n"
            "Obuna bo'lgandan so'ng '✅ Obunani tekshirish' tugmasini bosing.",
            reply_markup=get_subscription_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Check if user exists in database
    # async with async_session() as session:
    #     user = await session.get(User, user_id)
    
    user_exists = False  # Replace with actual DB check
    
    if not user_exists:
        # Create new user
        login, password = generate_credentials()
        
        # Save to database
        # new_user = User(
        #     telegram_id=user_id,
        #     username=message.from_user.username,
        #     login=login,
        #     password_hash=hash_password(password),
        #     balance=0.0
        # )
        # session.add(new_user)
        # await session.commit()
        
        await message.answer(
            "🎉 <b>Ro'yxatdan o'tdingiz!</b>\n\n"
            f"🔐 <b>Kirish ma'lumotlari:</b>\n"
            f"Login: <code>{login}</code>\n"
            f"Parol: <code>{password}</code>\n\n"
            "⚠️ <b>Bu ma'lumotlarni saqlang!</b>\n"
            "Web App'ga kirish uchun kerak bo'ladi.\n\n"
            "Pastdagi '🎰 O'yinlar' tugmasini bosing.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "👋 <b>Xush kelibsiz!</b>\n\n"
            "Quyidagi menyu orqali botdan foydalaning:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu"""
    await message.answer(
        "📋 <b>Asosiy menyu</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# ========================
# CALLBACK HANDLERS
# ========================

@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    """Check subscription callback"""
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        await callback.message.edit_text(
            "✅ <b>Obuna tasdiqlandi!</b>\n\n"
            "/start ni bosing.",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    """Show user profile"""
    user_id = callback.from_user.id
    
    # Get user from DB
    # async with async_session() as session:
    #     user = await session.get(User, user_id)
    
    # Example data
    profile_text = (
        "👤 <b>Profil Ma'lumotlari</b>\n\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"👤 Login: <code>user_12345678</code>\n"
        f"💰 Balans: <b>1,000.00 UZS</b>\n"
        f"📈 Jami yutuq: <b>5,000.00 UZS</b>\n"
        f"📉 Jami yutqazish: <b>3,500.00 UZS</b>\n"
        f"📅 Ro'yxatdan o'tgan: 2026-01-15\n"
    )
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "balance")
async def balance_callback(callback: CallbackQuery):
    """Show balance"""
    balance_text = (
        "💰 <b>Balans Ma'lumotlari</b>\n\n"
        f"Joriy balans: <b>1,000.00 UZS</b>\n"
        f"Muzlatilgan: <b>0.00 UZS</b>\n"
        f"Jami: <b>1,000.00 UZS</b>\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ To'ldirish", callback_data="deposit"),
            InlineKeyboardButton(text="➖ Yechish", callback_data="withdraw")
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        balance_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "deposit")
async def deposit_callback(callback: CallbackQuery, state: FSMContext):
    """Start deposit process"""
    await callback.message.edit_text(
        "➕ <b>Balans to'ldirish</b>\n\n"
        "To'ldirmoqchi bo'lgan summani kiriting (UZS):\n\n"
        "Misol: 50000",
        parse_mode="HTML"
    )
    
    await state.set_state(DepositStates.waiting_for_amount)


@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    """Process deposit amount"""
    try:
        amount = float(message.text)
        
        if amount < 10000:
            await message.answer("❌ Minimal summa: 10,000 UZS")
            return
        
        # Create deposit request in DB
        # request = DepositRequest(
        #     user_id=message.from_user.id,
        #     amount=amount,
        #     status='pending'
        # )
        
        # Notify admins
        for admin_id in ADMIN_IDS:
            admin_text = (
                "💳 <b>Yangi to'ldirish so'rovi</b>\n\n"
                f"👤 User ID: {message.from_user.id}\n"
                f"👤 Username: @{message.from_user.username}\n"
                f"💰 Summa: {amount:,.2f} UZS\n"
                f"🕐 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_deposit_{message.from_user.id}_{amount}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_deposit_{message.from_user.id}")
                ]
            ])
            
            await bot.send_message(admin_id, admin_text, reply_markup=keyboard, parse_mode="HTML")
        
        await message.answer(
            "✅ <b>So'rovingiz adminga yuborildi!</b>\n\n"
            "Admin tasdiqlagach balans tushadi.\n"
            "Biroz kuting...",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting.")


@router.callback_query(F.data == "withdraw")
async def withdraw_callback(callback: CallbackQuery, state: FSMContext):
    """Start withdrawal process"""
    await callback.message.edit_text(
        "➖ <b>Balansni yechish</b>\n\n"
        "Yechmoqchi bo'lgan summani kiriting (UZS):\n\n"
        "Misol: 50000",
        parse_mode="HTML"
    )
    
    await state.set_state(WithdrawalStates.waiting_for_amount)


@router.message(WithdrawalStates.waiting_for_amount)
async def process_withdrawal_amount(message: Message, state: FSMContext):
    """Process withdrawal amount"""
    try:
        amount = float(message.text)
        
        # Check user balance
        # user = await session.get(User, message.from_user.id)
        # if user.balance < amount:
        #     await message.answer("❌ Balansda yetarli mablag' yo'q!")
        #     return
        
        # Create withdrawal request
        # Similar to deposit...
        
        await message.answer(
            "✅ <b>Yechish so'rovi yuborildi!</b>\n\n"
            "Admin ko'rib chiqadi.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format!")


@router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    """Show user statistics"""
    stats_text = (
        "📊 <b>Statistika</b>\n\n"
        "🎮 Jami o'yinlar: <b>156</b>\n"
        "✅ Yutgan o'yinlar: <b>89</b>\n"
        "❌ Yutqazgan o'yinlar: <b>67</b>\n"
        "📈 Eng katta yutuq: <b>5,000.00 UZS</b>\n"
        "⚡️ Eng yuqori koeffitsient: <b>12.50x</b>\n"
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Show help information"""
    help_text = (
        "ℹ️ <b>Yordam</b>\n\n"
        "🎰 <b>O'yinlar:</b>\n"
        "• Aviator - Samolyot uchguncha cash out qiling\n"
        "• Apple of Fortune - Yashil olmani toping\n"
        "• Mines - Minalardan qoching\n\n"
        "💰 <b>Balans:</b>\n"
        "• To'ldirish - Admin orqali\n"
        "• Yechish - Admin orqali\n\n"
        "📞 <b>Qo'llab-quvvatlash:</b>\n"
        "@admin_username"
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    """Return to main menu"""
    await callback.message.edit_text(
        "📋 <b>Asosiy menyu</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# ========================
# ADMIN CALLBACKS
# ========================

@router.callback_query(F.data.startswith("approve_deposit_"))
async def approve_deposit_callback(callback: CallbackQuery):
    """Admin approves deposit"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    # Parse callback data
    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = float(parts[3])
    
    # Update user balance in DB
    # user = await session.get(User, user_id)
    # user.balance += amount
    # await session.commit()
    
    # Notify user
    await bot.send_message(
        user_id,
        f"✅ <b>To'lov tasdiqlandi!</b>\n\n"
        f"💰 Balans to'ldirildi: +{amount:,.2f} UZS\n"
        f"💳 Yangi balans: {amount:,.2f} UZS",
        parse_mode="HTML"
    )
    
    await callback.message.edit_text(
        f"✅ To'lov tasdiqlandi!\n\n"
        f"User: {user_id}\n"
        f"Summa: {amount:,.2f} UZS",
        parse_mode="HTML"
    )


# ========================
# MAIN
# ========================

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
