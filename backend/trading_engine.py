"""
KJBot Trading Engine
바이낸스/업비트 거래 실행 엔진
"""

import ccxt
import logging
from typing import Dict, Any, Optional, Literal
from config_manager import config_manager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingEngine:
    """거래 실행 엔진"""
    
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.config = config_manager.load_config()
        self.initialize_exchanges()
    
    def initialize_exchanges(self):
        """거래소 초기화"""
        # Binance 초기화
        binance_keys = config_manager.get_api_keys("binance")
        if binance_keys:
            try:
                self.exchanges["binance"] = ccxt.binance({
                    'apiKey': binance_keys['api_key'],
                    'secret': binance_keys['secret_key'],
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',  # 선물 거래
                    }
                })
                logger.info("✅ Binance 연결 성공")
            except Exception as e:
                logger.error(f"❌ Binance 초기화 실패: {e}")
        
        # Upbit 초기화
        upbit_keys = config_manager.get_api_keys("upbit")
        if upbit_keys:
            try:
                self.exchanges["upbit"] = ccxt.upbit({
                    'apiKey': upbit_keys['api_key'],
                    'secret': upbit_keys['secret_key'],
                    'enableRateLimit': True,
                })
                logger.info("✅ Upbit 연결 성공")
            except Exception as e:
                logger.error(f"❌ Upbit 초기화 실패: {e}")
    
    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        TradingView 시그널 실행
        
        Args:
            signal: {
                "action": "long_entry" | "short_entry" | "long_exit" | "short_exit",
                "symbol": "BTCUSDT",
                "exchange": "binance" | "upbit",
                "leverage": 10,
                "amount": 100,  # USDT
                "percent": 50   # 포지션의 50% 청산
            }
        
        Returns:
            실행 결과
        """
        try:
            action = signal.get("action")
            symbol = signal.get("symbol", "BTCUSDT")
            exchange_name = signal.get("exchange", "binance").lower()
            
            # 거래 활성화 확인
            if not self.config["trading"]["enable_trading"]:
                return {
                    "success": False,
                    "message": "⚠️ 거래가 비활성화되어 있습니다",
                    "signal": signal
                }
            
            # 거래소 확인
            if exchange_name not in self.exchanges:
                return {
                    "success": False,
                    "message": f"❌ {exchange_name} 거래소가 연결되지 않았습니다",
                    "signal": signal
                }
            
            exchange = self.exchanges[exchange_name]
            
            # [복리 모드] 퍼센트(%) 기반 진입 금액 계산
            if "percent" in signal and "amount" not in signal and "entry" in action:
                try:
                    balance = exchange.fetch_balance()
                    if 'USDT' in balance['free']:
                        free_usdt = balance['free']['USDT']
                        # 진입 금액(Margin) = 사용 가능 USDT * (설정 비율 / 100)
                        calculated_amount = free_usdt * (float(signal['percent']) / 100.0)
                        # 최소 주문 금액 안전장치 (10달러)
                        if calculated_amount < 10:
                            logger.warning(f"⚠️ 계산된 금액({calculated_amount:.2f})이 너무 작아 최소금액 11 USDT로 조정합니다.")
                            calculated_amount = 11
                        
                        signal['amount'] = round(calculated_amount, 2)
                        
                        logger.info(f"💰 복리 계산: 잔고 {free_usdt:.2f} USDT 중 {signal['percent']}% 사용 = {signal['amount']} USDT")
                    else:
                        logger.error("❌ USDT 잔고를 찾을 수 없습니다. 기본값 100 USDT를 사용합니다.")
                        signal['amount'] = 100
                except Exception as e:
                    logger.error(f"❌ 복리 금액 계산 실패: {e}")
                    signal['amount'] = 100  # 실패 시 안전장치
            
            # 액션별 처리
            if action == "long_entry":
                return self._execute_long_entry(exchange, symbol, signal)
            elif action == "short_entry":
                return self._execute_short_entry(exchange, symbol, signal)
            elif action == "long_exit":
                return self._execute_long_exit(exchange, symbol, signal)
            elif action == "short_exit":
                return self._execute_short_exit(exchange, symbol, signal)
            else:
                return {
                    "success": False,
                    "message": f"❌ 알 수 없는 액션: {action}",
                    "signal": signal
                }
        
        except Exception as e:
            logger.error(f"❌ 시그널 실행 실패: {e}")
            return {
                "success": False,
                "message": f"❌ 실행 오류: {str(e)}",
                "signal": signal
            }
    
    def _execute_long_entry(self, exchange: ccxt.Exchange, symbol: str, signal: Dict) -> Dict:
        """롱 진입"""
        try:
            leverage = signal.get("leverage", self.config["trading"]["default_leverage"])
            amount_usdt = signal.get("amount", 100)
            
            # 레버리지 설정 (Binance Futures)
            if isinstance(exchange, ccxt.binance):
                exchange.set_leverage(leverage, symbol)
            
            # 현재 가격 조회
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # 수량 계산
            quantity = (amount_usdt * leverage) / current_price
            
            # 시장가 매수 주문
            order = exchange.create_market_buy_order(symbol, quantity)
            
            logger.info(f"🟢 롱 진입 성공: {symbol} | 수량: {quantity:.6f} | 가격: {current_price}")
            
            return {
                "success": True,
                "message": f"🟢 롱 진입 성공",
                "order": order,
                "signal": signal,
                "details": {
                    "symbol": symbol,
                    "side": "buy",
                    "quantity": quantity,
                    "price": current_price,
                    "leverage": leverage
                }
            }
        
        except Exception as e:
            logger.error(f"❌ 롱 진입 실패: {e}")
            return {
                "success": False,
                "message": f"❌ 롱 진입 실패: {str(e)}",
                "signal": signal
            }
    
    def _execute_short_entry(self, exchange: ccxt.Exchange, symbol: str, signal: Dict) -> Dict:
        """숏 진입"""
        try:
            leverage = signal.get("leverage", self.config["trading"]["default_leverage"])
            amount_usdt = signal.get("amount", 100)
            
            # 레버리지 설정 (Binance Futures)
            if isinstance(exchange, ccxt.binance):
                exchange.set_leverage(leverage, symbol)
            
            # 현재 가격 조회
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # 수량 계산
            quantity = (amount_usdt * leverage) / current_price
            
            # 시장가 매도 주문
            order = exchange.create_market_sell_order(symbol, quantity)
            
            logger.info(f"🔴 숏 진입 성공: {symbol} | 수량: {quantity:.6f} | 가격: {current_price}")
            
            return {
                "success": True,
                "message": f"🔴 숏 진입 성공",
                "order": order,
                "signal": signal,
                "details": {
                    "symbol": symbol,
                    "side": "sell",
                    "quantity": quantity,
                    "price": current_price,
                    "leverage": leverage
                }
            }
        
        except Exception as e:
            logger.error(f"❌ 숏 진입 실패: {e}")
            return {
                "success": False,
                "message": f"❌ 숏 진입 실패: {str(e)}",
                "signal": signal
            }
    
    def _execute_long_exit(self, exchange: ccxt.Exchange, symbol: str, signal: Dict) -> Dict:
        """롱 청산 (익절/손절)"""
        try:
            percent = signal.get("percent", 100)  # 기본 100% 청산
            
            # 현재 포지션 조회
            positions = exchange.fetch_positions([symbol])
            long_position = next((p for p in positions if p['side'] == 'long'), None)
            
            if not long_position or long_position['contracts'] == 0:
                return {
                    "success": False,
                    "message": "⚠️ 청산할 롱 포지션이 없습니다",
                    "signal": signal
                }
            
            # 청산 수량 계산
            position_size = long_position['contracts']
            close_quantity = position_size * (percent / 100)
            
            # 시장가 매도 주문 (포지션 청산)
            order = exchange.create_market_sell_order(symbol, close_quantity, {
                'reduceOnly': True
            })
            
            logger.info(f"🟢 롱 청산 성공: {symbol} | 수량: {close_quantity:.6f} ({percent}%)")
            
            return {
                "success": True,
                "message": f"🟢 롱 청산 성공 ({percent}%)",
                "order": order,
                "signal": signal,
                "details": {
                    "symbol": symbol,
                    "side": "sell",
                    "quantity": close_quantity,
                    "percent": percent
                }
            }
        
        except Exception as e:
            logger.error(f"❌ 롱 청산 실패: {e}")
            return {
                "success": False,
                "message": f"❌ 롱 청산 실패: {str(e)}",
                "signal": signal
            }
    
    def _execute_short_exit(self, exchange: ccxt.Exchange, symbol: str, signal: Dict) -> Dict:
        """숏 청산 (익절/손절)"""
        try:
            percent = signal.get("percent", 100)  # 기본 100% 청산
            
            # 현재 포지션 조회
            positions = exchange.fetch_positions([symbol])
            short_position = next((p for p in positions if p['side'] == 'short'), None)
            
            if not short_position or short_position['contracts'] == 0:
                return {
                    "success": False,
                    "message": "⚠️ 청산할 숏 포지션이 없습니다",
                    "signal": signal
                }
            
            # 청산 수량 계산
            position_size = short_position['contracts']
            close_quantity = position_size * (percent / 100)
            
            # 시장가 매수 주문 (포지션 청산)
            order = exchange.create_market_buy_order(symbol, close_quantity, {
                'reduceOnly': True
            })
            
            logger.info(f"🔴 숏 청산 성공: {symbol} | 수량: {close_quantity:.6f} ({percent}%)")
            
            return {
                "success": True,
                "message": f"🔴 숏 청산 성공 ({percent}%)",
                "order": order,
                "signal": signal,
                "details": {
                    "symbol": symbol,
                    "side": "buy",
                    "quantity": close_quantity,
                    "percent": percent
                }
            }
        
        except Exception as e:
            logger.error(f"❌ 숏 청산 실패: {e}")
            return {
                "success": False,
                "message": f"❌ 숏 청산 실패: {str(e)}",
                "signal": signal
            }
    
    def get_balance(self, exchange_name: str = "binance") -> Optional[Dict]:
        """잔고 조회"""
        if exchange_name not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_name]
            balance = exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"❌ 잔고 조회 실패: {e}")
            return None
    
    def get_positions(self, exchange_name: str = "binance") -> Optional[list]:
        """포지션 조회"""
        if exchange_name not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_name]
            positions = exchange.fetch_positions()
            # 포지션이 있는 것만 필터링
            return [p for p in positions if p['contracts'] > 0]
        except Exception as e:
            logger.error(f"❌ 포지션 조회 실패: {e}")
            return None


# 싱글톤 인스턴스
trading_engine = TradingEngine()


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 TradingEngine 테스트")
    
    # 테스트 시그널
    test_signal = {
        "action": "long_entry",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "leverage": 10,
        "amount": 100
    }
    
    # 주의: 실제 거래가 실행되므로 테스트 시 주의!
    # result = trading_engine.execute_signal(test_signal)
    # print(f"실행 결과: {result}")
    
    print("⚠️  실제 거래 테스트는 주석을 해제하고 실행하세요")
