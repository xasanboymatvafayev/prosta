"""
CASINO PLATFORM - FASTAPI BACKEND
Main application with all endpoints
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import json
from pydantic import BaseModel

# Import models (assuming they're in separate file)
# from models import User, Transaction, GameSession, etc.

app = FastAPI(title="Casino Platform API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "95951223sabriyaevna2024secretkey"
ALGORITHM = "HS256"

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()


# ========================
# PYDANTIC SCHEMAS
# ========================

class UserLogin(BaseModel):
    login: str
    password: str

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    login: str
    balance: float
    total_won: float
    total_lost: float
    created_at: datetime

class GameBetRequest(BaseModel):
    game_type: str  # aviator, apple_of_fortune, mines
    bet_amount: float
    game_settings: Optional[dict] = None  # For mines: num_mines, etc.

class AviatorCashOutRequest(BaseModel):
    session_id: int
    multiplier: float

class MinesRevealRequest(BaseModel):
    session_id: int
    position: int

class ApplePickRequest(BaseModel):
    session_id: int
    level: int

class DepositRequest(BaseModel):
    amount: float

class WithdrawalRequest(BaseModel):
    amount: float


# ========================
# AUTHENTICATION
# ========================

def create_access_token(data: dict) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# ========================
# DATABASE DEPENDENCY
# ========================

def get_db():
    """Database session dependency"""
    # This should connect to your actual database
    # Example with SQLAlchemy:
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    pass


# ========================
# AUTH ENDPOINTS
# ========================

@app.post("/api/auth/login")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    User login with credentials from Telegram bot
    """
    # Find user by login
    # user = db.query(User).filter(User.login == credentials.login).first()
    
    # Placeholder response
    user_data = {
        "id": 1,
        "telegram_id": 123456789,
        "login": credentials.login
    }
    
    # Verify password
    # if not user or not verify_password(credentials.password, user.password_hash):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_access_token(user_data)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }


@app.get("/api/auth/me")
async def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current user info"""
    return {
        "user_id": token_data.get("id"),
        "login": token_data.get("login")
    }


# ========================
# USER ENDPOINTS
# ========================

@app.get("/api/user/profile")
async def get_profile(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Get user profile"""
    # user = db.query(User).filter(User.id == token_data['id']).first()
    
    return {
        "id": 1,
        "telegram_id": 123456789,
        "login": "user_12345",
        "balance": 1000.50,
        "total_won": 5000.00,
        "total_lost": 3500.00,
        "created_at": datetime.utcnow(),
        "status": "active"
    }


@app.get("/api/user/balance")
async def get_balance(token_data: dict = Depends(verify_token)):
    """Get current balance"""
    return {
        "balance": 1000.50,
        "currency": "UZS"
    }


# ========================
# GAME ENDPOINTS
# ========================

@app.post("/api/game/start")
async def start_game(
    bet_request: GameBetRequest,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Start a new game session
    """
    user_id = token_data['id']
    
    # Verify user has sufficient balance
    # user = db.query(User).filter(User.id == user_id).first()
    # if user.balance < bet_request.bet_amount:
    #     raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create game session
    # Import RNG based on game type
    from rng_engine import AviatorRNG, MinesRNG, AppleOfFortuneRNG
    
    game_data = {}
    
    if bet_request.game_type == "aviator":
        rng = AviatorRNG()
        crash_point = rng.generate_crash_point()
        game_data = {
            "crash_point": crash_point,
            "started_at": datetime.utcnow().timestamp()
        }
    
    elif bet_request.game_type == "mines":
        num_mines = bet_request.game_settings.get("num_mines", 3)
        rng = MinesRNG()
        mine_positions = rng.generate_mine_positions(num_mines)
        game_data = {
            "num_mines": num_mines,
            "mine_positions": mine_positions,  # This should be encrypted!
            "revealed_positions": []
        }
    
    elif bet_request.game_type == "apple_of_fortune":
        rng = AppleOfFortuneRNG()
        game_sequence = rng.generate_full_game()
        game_data = {
            "game_sequence": game_sequence,
            "current_level": 1
        }
    
    # Save to database
    # session = GameSession(
    #     user_id=user_id,
    #     game_type=bet_request.game_type,
    #     bet_amount=bet_request.bet_amount,
    #     game_data=json.dumps(game_data)
    # )
    # db.add(session)
    # db.commit()
    
    return {
        "session_id": 123,
        "game_type": bet_request.game_type,
        "bet_amount": bet_request.bet_amount,
        "status": "active",
        "game_data": game_data  # Client gets non-sensitive data only
    }


@app.post("/api/game/aviator/cashout")
async def aviator_cashout(
    cashout: AviatorCashOutRequest,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Cash out from Aviator game"""
    # Get game session
    # session = db.query(GameSession).filter(GameSession.id == cashout.session_id).first()
    
    # game_data = json.loads(session.game_data)
    # crash_point = game_data['crash_point']
    
    # Verify cashout is valid
    crash_point = 5.23  # Example
    if cashout.multiplier >= crash_point:
        # Too late, plane crashed
        return {
            "success": False,
            "message": "Plane crashed!",
            "crash_point": crash_point,
            "win_amount": 0
        }
    
    # Calculate win
    # win_amount = session.bet_amount * cashout.multiplier
    win_amount = 100 * cashout.multiplier
    
    # Update user balance
    # user.balance += win_amount
    # session.win_amount = win_amount
    # session.is_win = True
    # db.commit()
    
    return {
        "success": True,
        "multiplier": cashout.multiplier,
        "win_amount": win_amount,
        "new_balance": 1500.00
    }


@app.post("/api/game/mines/reveal")
async def mines_reveal(
    reveal: MinesRevealRequest,
    token_data: dict = Depends(verify_token)
):
    """Reveal a position in Mines game"""
    # Get session and check position
    # session = db.query(GameSession).filter(GameSession.id == reveal.session_id).first()
    # game_data = json.loads(session.game_data)
    
    mine_positions = [3, 7, 15, 21, 24]  # Example
    is_mine = reveal.position in mine_positions
    
    if is_mine:
        # Game over
        return {
            "is_mine": True,
            "position": reveal.position,
            "game_over": True,
            "win_amount": 0
        }
    else:
        # Safe cell
        from rng_engine import MinesRNG
        rng = MinesRNG()
        cells_opened = 3  # Example
        multiplier = rng.calculate_multiplier(5, cells_opened)
        
        return {
            "is_mine": False,
            "position": reveal.position,
            "multiplier": multiplier,
            "game_over": False
        }


@app.post("/api/game/apple/pick")
async def apple_pick(
    pick: ApplePickRequest,
    token_data: dict = Depends(verify_token)
):
    """Pick an apple in Apple of Fortune"""
    # session = db.query(GameSession).filter(GameSession.id == pick.session_id).first()
    # game_data = json.loads(session.game_data)
    # game_sequence = game_data['game_sequence']
    
    # Check if level result is green or red
    level_result = (pick.level, True, 1.5)  # Example: (level, is_green, multiplier)
    
    is_green = level_result[1]
    multiplier = level_result[2]
    
    if is_green:
        return {
            "is_green": True,
            "level": pick.level,
            "multiplier": multiplier,
            "can_continue": True
        }
    else:
        return {
            "is_green": False,
            "level": pick.level,
            "game_over": True,
            "win_amount": 0
        }


# ========================
# BALANCE ENDPOINTS
# ========================

@app.post("/api/balance/deposit")
async def request_deposit(
    deposit: DepositRequest,
    token_data: dict = Depends(verify_token)
):
    """Request balance deposit"""
    # Create deposit request
    # request = DepositRequest(
    #     user_id=token_data['id'],
    #     amount=deposit.amount,
    #     status='pending'
    # )
    # db.add(request)
    # db.commit()
    
    # Notify admin via bot
    
    return {
        "request_id": 456,
        "amount": deposit.amount,
        "status": "pending",
        "message": "So'rovingiz adminga yuborildi"
    }


@app.post("/api/balance/withdraw")
async def request_withdrawal(
    withdrawal: WithdrawalRequest,
    token_data: dict = Depends(verify_token)
):
    """Request balance withdrawal"""
    return {
        "request_id": 789,
        "amount": withdrawal.amount,
        "status": "pending",
        "message": "Pul yechish so'rovi yuborildi"
    }


# ========================
# WEBSOCKET FOR REAL-TIME UPDATES
# ========================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket for real-time game updates
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message['type'] == 'aviator_update':
                # Send current multiplier
                await manager.send_personal_message({
                    "type": "multiplier_update",
                    "multiplier": 2.35
                }, user_id)
            
            elif message['type'] == 'ping':
                await manager.send_personal_message({
                    "type": "pong"
                }, user_id)
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# ========================
# ADMIN ENDPOINTS
# ========================

@app.post("/api/admin/deposit/approve/{request_id}")
async def approve_deposit(request_id: int, token_data: dict = Depends(verify_token)):
    """Admin approves deposit request"""
    # Verify admin
    # Update deposit request status
    # Add balance to user
    
    return {
        "success": True,
        "message": "Deposit approved"
    }


@app.post("/api/admin/withdrawal/approve/{request_id}")
async def approve_withdrawal(request_id: int, token_data: dict = Depends(verify_token)):
    """Admin approves withdrawal request"""
    return {
        "success": True,
        "message": "Withdrawal approved"
    }


@app.get("/api/admin/stats")
async def get_admin_stats(token_data: dict = Depends(verify_token)):
    """Get admin statistics"""
    return {
        "total_users": 1523,
        "active_today": 342,
        "total_balance": 1234567.89,
        "total_profit": 45678.90,
        "pending_deposits": 12,
        "pending_withdrawals": 5
    }


# ========================
# HEALTH CHECK
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
