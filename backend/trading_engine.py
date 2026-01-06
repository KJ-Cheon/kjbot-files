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
            
            # 심볼 정규화 (바이낸스 선물 형식으로 변환)
            # TradingView에서 "GASUSDT.P" 형식으로 올 수 있으므로 ".P" 제거
            if exchange_name == "binance":
                symbol = symbol.replace(".P", "").upper()
            
            logger.info(f"📊 처리할 심볼: {symbol} (원본: {signal.get('symbol', 'N/A')})")
            
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
    
    def _normalize_symbol(self, exchange: ccxt.Exchange, symbol: str) -> str:
        """심볼 정규화 (거래소 형식에 맞게 변환)"""
        try:
            original_symbol = symbol
            # 바이낸스 선물: "GASUSDT.P" -> "GASUSDT"
            symbol = symbol.replace(".P", "").upper()
            
            if isinstance(exchange, ccxt.binance):
                # ccxt 마켓 정보 로드
                markets = exchange.load_markets()
                
                # 직접 매칭 시도
                if symbol in markets:
                    market_id = markets[symbol]['id']
                    logger.debug(f"✅ 심볼 매칭: {original_symbol} -> {symbol} -> {market_id}")
                    return market_id
                
                # ccxt 통합 형식으로 시도 (예: "GAS/USDT:USDT")
                unified_symbol = symbol
                if len(symbol) > 4 and symbol.endswith("USDT"):
                    base = symbol[:-4]
                    unified_symbol = f"{base}/USDT:USDT"
                    if unified_symbol in markets:
                        market_id = markets[unified_symbol]['id']
                        logger.debug(f"✅ 통합 형식 매칭: {original_symbol} -> {unified_symbol} -> {market_id}")
                        return market_id
                
                # 매칭 실패 시 원본 심볼 반환 (ccxt가 자동 처리)
                logger.warning(f"⚠️ 심볼 매칭 실패, 원본 사용: {original_symbol} -> {symbol}")
                return symbol
            
            return symbol
        except Exception as e:
            logger.warning(f"⚠️ 심볼 정규화 실패, 원본 사용: {symbol} ({e})")
            return symbol.replace(".P", "").upper()
    
    def _get_position(self, exchange: ccxt.Exchange, symbol: str, side: str) -> Optional[Dict]:
        """포지션 조회 헬퍼 함수"""
        try:
            # 심볼 정규화
            normalized_symbol = self._normalize_symbol(exchange, symbol)
            positions = exchange.fetch_positions([normalized_symbol])
            position = next((p for p in positions if p['side'] == side), None)
            if position and position['contracts'] > 0:
                return position
            return None
        except Exception as e:
            logger.error(f"❌ 포지션 조회 실패: {symbol} -> {normalized_symbol if 'normalized_symbol' in locals() else 'N/A'} ({e})")
            return None
    
    def _execute_long_entry(self, exchange: ccxt.Exchange, symbol: str, signal: Dict) -> Dict:
        """롱 진입"""
        try:
            # 기존 포지션 확인
            long_position = self._get_position(exchange, symbol, 'long')
            short_position = self._get_position(exchange, symbol, 'short')
            
            # 같은 방향 포지션이 있으면 차단
            if long_position:
                return {
                    "success": False,
                    "message": "⚠️ 이미 롱 포지션이 있습니다. 분할 청산(long_exit)을 사용하세요.",
                    "signal": signal
                }
            
            # 반대 포지션이 있으면 먼저 100% 청산
            if short_position:
                logger.info(f"🔄 숏 포지션 감지 → 100% 청산 후 롱 진입")
                close_result = self._execute_short_exit(exchange, symbol, {"percent": 100})
                if not close_result["success"]:
                    return {
                        "success": False,
                        "message": f"❌ 기존 숏 포지션 청산 실패: {close_result['message']}",
                        "signal": signal
                    }
                logger.info(f"✅ 숏 포지션 청산 완료 → 롱 진입 진행")
            
            leverage = signal.get("leverage", self.config["trading"]["default_leverage"])
            amount_usdt = signal.get("amount", 100)
            
            # 심볼 정규화
            normalized_symbol = self._normalize_symbol(exchange, symbol)
            logger.info(f"🔧 심볼 정규화: {symbol} -> {normalized_symbol}")
            
            # 레버리지 설정 (Binance Futures)
            if isinstance(exchange, ccxt.binance):
                try:
                    exchange.set_leverage(leverage, normalized_symbol)
                    logger.info(f"⚙️ 레버리지 설정: {leverage}x ({normalized_symbol})")
                except Exception as e:
                    logger.warning(f"⚠️ 레버리지 설정 실패 (계속 진행): {e}")
            
            # 현재 가격 조회
            ticker = exchange.fetch_ticker(normalized_symbol)
            current_price = ticker['last']
            logger.info(f"💰 현재 가격: {normalized_symbol} = {current_price}")
            
            # 수량 계산
            quantity = (amount_usdt * leverage) / current_price
            logger.info(f"📊 계산된 수량: {quantity:.6f} (금액: {amount_usdt} USDT, 레버리지: {leverage}x)")
            
            # 시장가 매수 주문
            order = exchange.create_market_buy_order(normalized_symbol, quantity)
            
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
            # 기존 포지션 확인
            long_position = self._get_position(exchange, symbol, 'long')
            short_position = self._get_position(exchange, symbol, 'short')
            
            # 같은 방향 포지션이 있으면 차단
            if short_position:
                return {
                    "success": False,
                    "message": "⚠️ 이미 숏 포지션이 있습니다. 분할 청산(short_exit)을 사용하세요.",
                    "signal": signal
                }
            
            # 반대 포지션이 있으면 먼저 100% 청산
            if long_position:
                logger.info(f"🔄 롱 포지션 감지 → 100% 청산 후 숏 진입")
                close_result = self._execute_long_exit(exchange, symbol, {"percent": 100})
                if not close_result["success"]:
                    return {
                        "success": False,
                        "message": f"❌ 기존 롱 포지션 청산 실패: {close_result['message']}",
                        "signal": signal
                    }
                logger.info(f"✅ 롱 포지션 청산 완료 → 숏 진입 진행")
            
            leverage = signal.get("leverage", self.config["trading"]["default_leverage"])
            amount_usdt = signal.get("amount", 100)
            
            # 심볼 정규화
            normalized_symbol = self._normalize_symbol(exchange, symbol)
            logger.info(f"🔧 심볼 정규화: {symbol} -> {normalized_symbol}")
            
            # 레버리지 설정 (Binance Futures)
            if isinstance(exchange, ccxt.binance):
                try:
                    exchange.set_leverage(leverage, normalized_symbol)
                    logger.info(f"⚙️ 레버리지 설정: {leverage}x ({normalized_symbol})")
                except Exception as e:
                    logger.warning(f"⚠️ 레버리지 설정 실패 (계속 진행): {e}")
            
            # 현재 가격 조회
            ticker = exchange.fetch_ticker(normalized_symbol)
            current_price = ticker['last']
            logger.info(f"💰 현재 가격: {normalized_symbol} = {current_price}")
            
            # 수량 계산
            quantity = (amount_usdt * leverage) / current_price
            logger.info(f"📊 계산된 수량: {quantity:.6f} (금액: {amount_usdt} USDT, 레버리지: {leverage}x)")
            
            # 시장가 매도 주문
            order = exchange.create_market_sell_order(normalized_symbol, quantity)
            
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
            
            # percent 값 검증 (0-100 범위)
            if percent <= 0 or percent > 100:
                return {
                    "success": False,
                    "message": f"⚠️ 청산 비율은 1-100% 사이여야 합니다. 입력값: {percent}%",
                    "signal": signal
                }
            
            # 현재 포지션 조회
            long_position = self._get_position(exchange, symbol, 'long')
            
            if not long_position:
                # 포지션이 없으면 경고만 로그하고 성공으로 처리 (트레이딩뷰와 실제 포지션 불일치 대응)
                logger.warning(f"⚠️ 청산할 롱 포지션이 없습니다 (이미 청산되었거나 존재하지 않음)")
                return {
                    "success": True,
                    "message": "ℹ️ 청산할 롱 포지션이 없습니다 (이미 처리됨)",
                    "signal": signal
                }
            
            # 청산 수량 계산
            position_size = long_position['contracts']
            close_quantity = position_size * (percent / 100)
            
            # 청산 수량 검증
            if close_quantity <= 0:
                return {
                    "success": False,
                    "message": f"⚠️ 계산된 청산 수량이 0 이하입니다. 포지션: {position_size}, 비율: {percent}%",
                    "signal": signal
                }
            
            if close_quantity > position_size:
                logger.warning(f"⚠️ 청산 수량({close_quantity})이 포지션 크기({position_size})보다 큽니다. 포지션 크기로 조정합니다.")
                close_quantity = position_size
            
            # 심볼 정규화
            normalized_symbol = self._normalize_symbol(exchange, symbol)
            logger.info(f"🔧 청산 심볼 정규화: {symbol} -> {normalized_symbol}")
            
            # 시장가 매도 주문 (포지션 청산)
            order = exchange.create_market_sell_order(normalized_symbol, close_quantity, {
                'reduceOnly': True
            })
            
            logger.info(f"🟢 롱 청산 성공: {symbol} | 수량: {close_quantity:.6f} / {position_size:.6f} ({percent}%)")
            
            return {
                "success": True,
                "message": f"🟢 롱 청산 성공 ({percent}%)",
                "order": order,
                "signal": signal,
                "details": {
                    "symbol": symbol,
                    "side": "sell",
                    "quantity": close_quantity,
                    "position_size": position_size,
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
            
            # percent 값 검증 (0-100 범위)
            if percent <= 0 or percent > 100:
                return {
                    "success": False,
                    "message": f"⚠️ 청산 비율은 1-100% 사이여야 합니다. 입력값: {percent}%",
                    "signal": signal
                }
            
            # 현재 포지션 조회
            short_position = self._get_position(exchange, symbol, 'short')
            
            if not short_position:
                # 포지션이 없으면 경고만 로그하고 성공으로 처리 (트레이딩뷰와 실제 포지션 불일치 대응)
                logger.warning(f"⚠️ 청산할 숏 포지션이 없습니다 (이미 청산되었거나 존재하지 않음)")
                return {
                    "success": True,
                    "message": "ℹ️ 청산할 숏 포지션이 없습니다 (이미 처리됨)",
                    "signal": signal
                }
            
            # 청산 수량 계산
            position_size = short_position['contracts']
            close_quantity = position_size * (percent / 100)
            
            # 청산 수량 검증
            if close_quantity <= 0:
                return {
                    "success": False,
                    "message": f"⚠️ 계산된 청산 수량이 0 이하입니다. 포지션: {position_size}, 비율: {percent}%",
                    "signal": signal
                }
            
            if close_quantity > position_size:
                logger.warning(f"⚠️ 청산 수량({close_quantity})이 포지션 크기({position_size})보다 큽니다. 포지션 크기로 조정합니다.")
                close_quantity = position_size
            
            # 심볼 정규화
            normalized_symbol = self._normalize_symbol(exchange, symbol)
            logger.info(f"🔧 청산 심볼 정규화: {symbol} -> {normalized_symbol}")
            
            # 시장가 매수 주문 (포지션 청산)
            order = exchange.create_market_buy_order(normalized_symbol, close_quantity, {
                'reduceOnly': True
            })
            
            logger.info(f"🔴 숏 청산 성공: {symbol} | 수량: {close_quantity:.6f} / {position_size:.6f} ({percent}%)")
            
            return {
                "success": True,
                "message": f"🔴 숏 청산 성공 ({percent}%)",
                "order": order,
                "signal": signal,
                "details": {
                    "symbol": symbol,
                    "side": "buy",
                    "quantity": close_quantity,
                    "position_size": position_size,
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
