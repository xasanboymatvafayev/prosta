import React, { useState, useEffect, useRef } from 'react';
import './frontend/AviatorGame.css';

/**
 * AVIATOR GAME COMPONENT
 * 1xBet style Aviator game with real-time multiplier
 */

const AviatorGame = () => {
  const [gameState, setGameState] = useState('waiting'); // waiting, flying, crashed
  const [multiplier, setMultiplier] = useState(1.00);
  const [betAmount, setBetAmount] = useState('');
  const [balance, setBalance] = useState(1000.00);
  const [cashOutMultiplier, setCashOutMultiplier] = useState(null);
  const [winAmount, setWinAmount] = useState(0);
  const [history, setHistory] = useState([]);
  const [countdown, setCountdown] = useState(5);
  
  const gameIntervalRef = useRef(null);
  const startTimeRef = useRef(null);
  const crashPointRef = useRef(null);
  const wsRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    const token = localStorage.getItem('token');
    const ws = new WebSocket(`wss://your-api.com/ws/${token}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'game_start') {
        startGame(data.crash_point);
      } else if (data.type === 'game_crash') {
        crashGame();
      }
    };
    
    wsRef.current = ws;
    
    return () => ws.close();
  }, []);

  // Start new game
  const startGame = (crashPoint) => {
    crashPointRef.current = crashPoint;
    startTimeRef.current = Date.now();
    setGameState('flying');
    setMultiplier(1.00);
    setCashOutMultiplier(null);
    setWinAmount(0);
    
    // Start multiplier increment
    gameIntervalRef.current = setInterval(() => {
      const elapsed = (Date.now() - startTimeRef.current) / 1000;
      const currentMult = calculateMultiplier(elapsed);
      
      setMultiplier(currentMult);
      
      // Check if reached crash point
      if (currentMult >= crashPointRef.current) {
        crashGame();
      }
    }, 50); // Update every 50ms for smooth animation
  };

  const calculateMultiplier = (seconds) => {
    // Aviator formula: exponential growth
    const baseRate = 0.1;
    const acceleration = 1.05;
    const mult = 1.0 + (baseRate * seconds * Math.pow(acceleration, seconds / 10));
    return parseFloat(mult.toFixed(2));
  };

  const crashGame = () => {
    clearInterval(gameIntervalRef.current);
    setGameState('crashed');
    
    // Add to history
    setHistory(prev => [crashPointRef.current, ...prev.slice(0, 19)]);
    
    // Start countdown for next game
    setCountdown(5);
    const countdownInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownInterval);
          setGameState('waiting');
          // Request new game from server
          requestNewGame();
          return 5;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const requestNewGame = async () => {
    // API call to start new game
    try {
      const response = await fetch('https://your-api.com/api/game/aviator/new', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      startGame(data.crash_point);
    } catch (error) {
      console.error('Error starting game:', error);
    }
  };

  const placeBet = async () => {
    const amount = parseFloat(betAmount);
    
    if (amount <= 0 || amount > balance) {
      alert('Noto\'g\'ri summa!');
      return;
    }
    
    try {
      const response = await fetch('https://your-api.com/api/game/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          game_type: 'aviator',
          bet_amount: amount
        })
      });
      
      const data = await response.json();
      setBalance(prev => prev - amount);
      
    } catch (error) {
      console.error('Error placing bet:', error);
    }
  };

  const cashOut = async () => {
    if (gameState !== 'flying' || cashOutMultiplier !== null) return;
    
    const currentMult = multiplier;
    setCashOutMultiplier(currentMult);
    
    try {
      const response = await fetch('https://your-api.com/api/game/aviator/cashout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: 123, // Get from game start
          multiplier: currentMult
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const win = parseFloat(betAmount) * currentMult;
        setWinAmount(win);
        setBalance(prev => prev + win);
      }
      
    } catch (error) {
      console.error('Error cashing out:', error);
    }
  };

  const getMultiplierColor = () => {
    if (gameState === 'crashed') return '#ef4444';
    if (multiplier < 2) return '#10b981';
    if (multiplier < 5) return '#f59e0b';
    return '#8b5cf6';
  };

  return (
    <div className="aviator-game">
      {/* Header */}
      <div className="game-header">
        <div className="balance-display">
          <span className="balance-label">Balans:</span>
          <span className="balance-amount">{balance.toFixed(2)} UZS</span>
        </div>
      </div>

      {/* Main Game Area */}
      <div className="game-canvas">
        <div className="sky-background">
          {/* Plane SVG */}
          <div className={`plane ${gameState === 'flying' ? 'flying' : ''}`}>
            ✈️
          </div>

          {/* Multiplier Display */}
          <div className="multiplier-display" style={{ color: getMultiplierColor() }}>
            {gameState === 'crashed' ? (
              <div className="crashed-text">
                <div className="crash-value">{crashPointRef.current}x</div>
                <div className="crash-label">CRASHED!</div>
              </div>
            ) : (
              <div className="current-multiplier">
                {multiplier.toFixed(2)}x
              </div>
            )}
          </div>

          {/* Countdown */}
          {gameState === 'waiting' && (
            <div className="countdown-display">
              Keyingi o'yin: {countdown}s
            </div>
          )}

          {/* Win Display */}
          {cashOutMultiplier && (
            <div className="win-display">
              <div className="win-mult">{cashOutMultiplier}x</div>
              <div className="win-amount">+{winAmount.toFixed(2)} UZS</div>
            </div>
          )}
        </div>

        {/* Graph (optional enhancement) */}
        <canvas id="aviator-graph" className="graph-canvas"></canvas>
      </div>

      {/* Betting Panel */}
      <div className="betting-panel">
        <div className="bet-input-group">
          <label>Tikish summasi:</label>
          <input
            type="number"
            value={betAmount}
            onChange={(e) => setBetAmount(e.target.value)}
            placeholder="1000"
            disabled={gameState === 'flying'}
            className="bet-input"
          />
          
          <div className="quick-bet-buttons">
            <button onClick={() => setBetAmount('1000')}>1K</button>
            <button onClick={() => setBetAmount('5000')}>5K</button>
            <button onClick={() => setBetAmount('10000')}>10K</button>
            <button onClick={() => setBetAmount('50000')}>50K</button>
          </div>
        </div>

        <div className="action-buttons">
          {gameState === 'waiting' ? (
            <button 
              className="bet-button"
              onClick={placeBet}
              disabled={!betAmount || parseFloat(betAmount) <= 0}
            >
              Tikish
            </button>
          ) : gameState === 'flying' && !cashOutMultiplier ? (
            <button 
              className="cashout-button"
              onClick={cashOut}
            >
              Cash Out ({multiplier.toFixed(2)}x)
            </button>
          ) : (
            <button className="waiting-button" disabled>
              Kutilmoqda...
            </button>
          )}
        </div>
      </div>

      {/* History */}
      <div className="game-history">
        <h3>Tarix</h3>
        <div className="history-items">
          {history.map((mult, index) => (
            <div 
              key={index} 
              className={`history-item ${mult >= 2 ? 'high' : 'low'}`}
            >
              {mult.toFixed(2)}x
            </div>
          ))}
        </div>
      </div>

      {/* Statistics */}
      <div className="game-stats">
        <div className="stat-item">
          <span className="stat-label">O'rtacha:</span>
          <span className="stat-value">
            {history.length > 0 
              ? (history.reduce((a, b) => a + b, 0) / history.length).toFixed(2) 
              : '0.00'}x
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Eng yuqori:</span>
          <span className="stat-value">
            {history.length > 0 ? Math.max(...history).toFixed(2) : '0.00'}x
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Eng past:</span>
          <span className="stat-value">
            {history.length > 0 ? Math.min(...history).toFixed(2) : '0.00'}x
          </span>
        </div>
      </div>
    </div>
  );
};

export default AviatorGame;
