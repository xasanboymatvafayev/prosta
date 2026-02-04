"""
Casino Platform - Database Models
PostgreSQL + SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class UserStatus(enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    FROZEN = "frozen"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    WIN = "win"
    LOSS = "loss"
    BONUS = "bonus"


class GameType(enum.Enum):
    AVIATOR = "aviator"
    APPLE_OF_FORTUNE = "apple_of_fortune"
    MINES = "mines"


# ========================
# USER MODEL
# ========================
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Balance
    balance = Column(Float, default=0.0)
    total_won = Column(Float, default=0.0)
    total_lost = Column(Float, default=0.0)
    
    # Status
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_subscribed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    game_sessions = relationship("GameSession", back_populates="user")
    withdrawal_requests = relationship("WithdrawalRequest", back_populates="user")


# ========================
# TRANSACTION MODEL
# ========================
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    
    # Additional info
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    description = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    game_session = relationship("GameSession", back_populates="transactions")


# ========================
# GAME SESSION MODEL
# ========================
class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    game_type = Column(Enum(GameType), nullable=False)
    bet_amount = Column(Float, nullable=False)
    win_amount = Column(Float, default=0.0)
    
    # Game specific data (JSON format)
    game_data = Column(Text, nullable=True)  # Stores game-specific details
    
    # Results
    multiplier = Column(Float, nullable=True)
    is_win = Column(Boolean, default=False)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="game_sessions")
    transactions = relationship("Transaction", back_populates="game_session")


# ========================
# WITHDRAWAL REQUEST MODEL
# ========================
class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Admin actions
    admin_id = Column(Integer, nullable=True)
    admin_comment = Column(String(500), nullable=True)
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="withdrawal_requests")


# ========================
# DEPOSIT REQUEST MODEL
# ========================
class DepositRequest(Base):
    __tablename__ = "deposit_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    
    admin_id = Column(Integer, nullable=True)
    
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


# ========================
# PROMO CODE MODEL
# ========================
class PromoCode(Base):
    __tablename__ = "promo_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    
    bonus_percentage = Column(Float, nullable=False)  # 10.0 = 10%
    bonus_amount = Column(Float, nullable=True)  # Fixed bonus
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    current_uses = Column(Integer, default=0)
    
    # Time limits
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    
    # Subscription requirement
    requires_subscription = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========================
# SUBSCRIPTION CHANNEL MODEL
# ========================
class SubscriptionChannel(Base):
    __tablename__ = "subscription_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(100), unique=True, nullable=False)
    channel_name = Column(String(200), nullable=False)
    channel_link = Column(String(300), nullable=False)
    
    is_required = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ========================
# ADVERTISEMENT MODEL
# ========================
class Advertisement(Base):
    __tablename__ = "advertisements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    ad_type = Column(String(20), nullable=False)  # banner, popup, message
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    
    # Display settings
    is_active = Column(Boolean, default=True)
    display_frequency = Column(Integer, default=1)  # Show every X sessions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# ========================
# ADMIN USER MODEL
# ========================
class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    
    role = Column(String(20), default="admin")  # admin, super_admin
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========================
# SYSTEM SETTINGS MODEL
# ========================
class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
