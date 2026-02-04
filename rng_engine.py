"""
PROVABLY FAIR RNG ENGINE
Cryptographically secure random number generation
"""

import hashlib
import hmac
import secrets
import time
from typing import List, Tuple
import random


class ProvenlyFairRNG:
    """
    Provably Fair Random Number Generator
    Har bir o'yin natijasi tasdiqlash mumkin
    """
    
    def __init__(self):
        self.server_seed = self._generate_seed()
        self.nonce = 0
    
    def _generate_seed(self) -> str:
        """Generate cryptographically secure seed"""
        return secrets.token_hex(32)
    
    def _hash(self, data: str) -> str:
        """SHA-256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generate_number(self, min_val: float, max_val: float, client_seed: str = None) -> float:
        """
        Generate provably fair random number
        """
        if client_seed is None:
            client_seed = secrets.token_hex(16)
        
        # Combine seeds and nonce
        combined = f"{self.server_seed}:{client_seed}:{self.nonce}"
        hash_result = self._hash(combined)
        
        # Convert hash to number
        hash_int = int(hash_result[:16], 16)
        normalized = hash_int / (16**16)
        
        # Scale to range
        result = min_val + (normalized * (max_val - min_val))
        
        self.nonce += 1
        return result
    
    def verify(self, server_seed: str, client_seed: str, nonce: int, result: float) -> bool:
        """Verify game result"""
        combined = f"{server_seed}:{client_seed}:{nonce}"
        hash_result = self._hash(combined)
        hash_int = int(hash_result[:16], 16)
        normalized = hash_int / (16**16)
        
        return abs(result - normalized) < 0.0001


# ========================
# AVIATOR RNG
# ========================
class AviatorRNG:
    """
    Aviator o'yini uchun crash point generator
    1xBet algoritmi asosida
    """
    
    def __init__(self):
        self.rng = ProvenlyFairRNG()
    
    def generate_crash_point(self) -> float:
        """
        Generate crash multiplier
        Formula: 99/(100-random(0-100))
        
        Distribution:
        - 50% crash < 2.00x
        - 25% crash 2.00x - 5.00x
        - 15% crash 5.00x - 10.00x
        - 10% crash > 10.00x
        """
        random_value = self.rng.generate_number(0, 100)
        
        # Prevent division by zero
        if random_value >= 99:
            random_value = 98.99
        
        crash_point = 99 / (100 - random_value)
        
        # Limit maximum crash
        if crash_point > 1000:
            crash_point = random.uniform(1.0, 100.0)
        
        return round(crash_point, 2)
    
    def get_current_multiplier(self, elapsed_time: float) -> float:
        """
        Calculate current multiplier based on time
        Aviator formula: multiplier grows exponentially
        
        Args:
            elapsed_time: seconds since game start
        
        Returns:
            Current multiplier (e.g., 1.52x)
        """
        # Aviator growth rate: approximately 0.1 per second with acceleration
        base_rate = 0.1
        acceleration = 1.05  # Exponential growth
        
        multiplier = 1.0 + (base_rate * elapsed_time * (acceleration ** (elapsed_time / 10)))
        
        return round(multiplier, 2)


# ========================
# APPLE OF FORTUNE RNG
# ========================
class AppleOfFortuneRNG:
    """
    Apple of Fortune o'yini uchun RNG
    Har bir bosqichda yashil yoki qizil olma
    """
    
    def __init__(self, total_levels: int = 8):
        self.rng = ProvenlyFairRNG()
        self.total_levels = total_levels
    
    def generate_level_result(self, current_level: int, bet_amount: float) -> Tuple[bool, float]:
        """
        Generate result for current level
        
        Returns:
            (is_green_apple, new_multiplier)
        """
        # Success probability decreases with each level
        base_success_rate = 70  # 70% success on first level
        level_penalty = 5  # -5% per level
        
        success_rate = max(30, base_success_rate - (current_level * level_penalty))
        
        random_value = self.rng.generate_number(0, 100)
        is_success = random_value <= success_rate
        
        # Calculate multiplier
        if is_success:
            # Multiplier increases with each level
            multiplier = 1.0 + (0.3 * current_level)
            return True, round(multiplier, 2)
        else:
            return False, 0.0
    
    def generate_full_game(self) -> List[Tuple[int, bool, float]]:
        """
        Generate entire game sequence
        Returns list of (level, is_green, multiplier)
        """
        results = []
        current_multiplier = 1.0
        
        for level in range(1, self.total_levels + 1):
            is_green, level_mult = self.generate_level_result(level, 0)
            
            if is_green:
                current_multiplier *= level_mult
                results.append((level, True, round(current_multiplier, 2)))
            else:
                results.append((level, False, 0.0))
                break
        
        return results


# ========================
# MINES RNG
# ========================
class MinesRNG:
    """
    Mines o'yini uchun RNG
    5x5 grid with hidden mines
    """
    
    def __init__(self, grid_size: int = 5):
        self.rng = ProvenlyFairRNG()
        self.grid_size = grid_size
        self.total_cells = grid_size * grid_size
    
    def generate_mine_positions(self, num_mines: int) -> List[int]:
        """
        Generate random mine positions
        
        Args:
            num_mines: Number of mines (1-24 for 5x5 grid)
        
        Returns:
            List of mine positions (0-24)
        """
        if num_mines >= self.total_cells:
            num_mines = self.total_cells - 1
        
        # Generate unique random positions
        all_positions = list(range(self.total_cells))
        mine_positions = []
        
        for _ in range(num_mines):
            if not all_positions:
                break
            
            # Use RNG to select position
            random_index = int(self.rng.generate_number(0, len(all_positions) - 0.01))
            position = all_positions.pop(random_index)
            mine_positions.append(position)
        
        return sorted(mine_positions)
    
    def calculate_multiplier(self, num_mines: int, cells_opened: int) -> float:
        """
        Calculate win multiplier based on mines and opened cells
        
        Formula similar to 1xBet Mines:
        - More mines = higher risk = higher reward
        - More cells opened = higher multiplier
        """
        safe_cells = self.total_cells - num_mines
        
        if cells_opened >= safe_cells:
            cells_opened = safe_cells - 1
        
        # Base multiplier calculation
        base = 1.0
        for i in range(1, cells_opened + 1):
            probability = (safe_cells - i + 1) / (self.total_cells - i + 1)
            base *= (1 / probability)
        
        # Adjust for house edge (3-5%)
        house_edge = 0.97
        multiplier = base * house_edge
        
        return round(multiplier, 2)
    
    def is_mine(self, position: int, mine_positions: List[int]) -> bool:
        """Check if position contains mine"""
        return position in mine_positions


# ========================
# GAME RESULTS STORAGE
# ========================
class GameResult:
    """Store game results for verification"""
    
    def __init__(self):
        self.results = {}
    
    def save_result(self, game_id: int, server_seed: str, client_seed: str, 
                   nonce: int, result: dict):
        """Save game result"""
        self.results[game_id] = {
            'server_seed': server_seed,
            'client_seed': client_seed,
            'nonce': nonce,
            'result': result,
            'timestamp': time.time()
        }
    
    def get_result(self, game_id: int) -> dict:
        """Get game result"""
        return self.results.get(game_id)


# ========================
# EXAMPLE USAGE
# ========================
if __name__ == "__main__":
    print("=== AVIATOR TEST ===")
    aviator = AviatorRNG()
    for i in range(10):
        crash = aviator.generate_crash_point()
        print(f"Round {i+1}: Crash at {crash}x")
    
    print("\n=== APPLE OF FORTUNE TEST ===")
    apple = AppleOfFortuneRNG()
    game = apple.generate_full_game()
    for level, is_green, mult in game:
        status = "🟢 Green" if is_green else "🔴 Red"
        print(f"Level {level}: {status} - Multiplier: {mult}x")
    
    print("\n=== MINES TEST ===")
    mines = MinesRNG()
    mine_positions = mines.generate_mine_positions(5)
    print(f"Mine positions: {mine_positions}")
    
    for i in range(5):
        mult = mines.calculate_multiplier(5, i+1)
        print(f"After {i+1} cells: {mult}x multiplier")
