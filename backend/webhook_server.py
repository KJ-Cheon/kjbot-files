"""
KJBot Webhook Server
TradingView 시그널을 받아서 거래 실행
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any
from config_manager import config_manager
from trading_engine import trading_engine

# Flask 앱 생성
app = Flask(__name__)
CORS(app)  # CORS 허용

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/kjbot/webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 설정 로드
config = config_manager.load_config()


def check_ip_whitelist(ip: str) -> bool:
    """IP 화이트리스트 확인"""
    if not config["security"]["require_ip_whitelist"]:
        return True
    
    allowed_ips = config["security"]["allowed_ips"]
    return ip in allowed_ips


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    TradingView Webhook 엔드포인트
    
    예상 JSON 형식:
    {
        "action": "long_entry",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "leverage": 10,
        "amount": 100
    }
    """
    try:
        # 클라이언트 IP 확인
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # IP 화이트리스트 체크
        if not check_ip_whitelist(client_ip):
            logger.warning(f"⚠️ 허용되지 않은 IP: {client_ip}")
            return jsonify({
                "success": False,
                "message": "Unauthorized IP address"
            }), 403
        
        # JSON 데이터 파싱
        if not request.is_json:
            logger.error("❌ JSON 형식이 아닙니다")
            return jsonify({
                "success": False,
                "message": "Content-Type must be application/json"
            }), 400
        
        signal = request.get_json()
        
        # 필수 필드 확인
        if "action" not in signal:
            logger.error("❌ action 필드가 없습니다")
            return jsonify({
                "success": False,
                "message": "Missing required field: action"
            }), 400
        
        logger.info(f"📨 Webhook 수신: {signal} (from {client_ip})")
        
        # 거래 실행
        result = trading_engine.execute_signal(signal)
        
        # 결과 로깅
        if result["success"]:
            logger.info(f"✅ 거래 성공: {result['message']}")
        else:
            logger.error(f"❌ 거래 실패: {result['message']}")
        
        return jsonify(result), 200 if result["success"] else 400
    
    except Exception as e:
        logger.error(f"❌ Webhook 처리 오류: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal server error: {str(e)}"
        }), 500


@app.route('/api/balance', methods=['GET'])
def get_balance():
    """잔고 조회 API"""
    try:
        exchange = request.args.get('exchange', 'binance')
        balance = trading_engine.get_balance(exchange)
        
        if balance is None:
            return jsonify({
                "success": False,
                "message": f"{exchange} 거래소가 연결되지 않았습니다"
            }), 400
        
        return jsonify({
            "success": True,
            "balance": balance
        })
    
    except Exception as e:
        logger.error(f"❌ 잔고 조회 오류: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """포지션 조회 API"""
    try:
        exchange = request.args.get('exchange', 'binance')
        positions = trading_engine.get_positions(exchange)
        
        if positions is None:
            return jsonify({
                "success": False,
                "message": f"{exchange} 거래소가 연결되지 않았습니다"
            }), 400
        
        return jsonify({
            "success": True,
            "positions": positions
        })
    
    except Exception as e:
        logger.error(f"❌ 포지션 조회 오류: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """설정 조회 API"""
    try:
        # 민감한 정보 제외
        safe_config = {
            "trading": config["trading"],
            "security": {
                "require_ip_whitelist": config["security"]["require_ip_whitelist"],
                "allowed_ips_count": len(config["security"]["allowed_ips"])
            }
        }
        
        return jsonify({
            "success": True,
            "config": safe_config
        })
    
    except Exception as e:
        logger.error(f"❌ 설정 조회 오류: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """설정 업데이트 API"""
    try:
        new_config = request.get_json()
        
        # 기존 설정과 병합
        config.update(new_config)
        
        # 저장
        config_manager.save_config(config)
        
        logger.info(f"✅ 설정 업데이트 완료")
        
        return jsonify({
            "success": True,
            "message": "설정이 업데이트되었습니다"
        })
    
    except Exception as e:
        logger.error(f"❌ 설정 업데이트 오류: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/keys', methods=['POST'])
def save_api_keys():
    """API 키 저장"""
    try:
        data = request.get_json()
        
        exchange = data.get('exchange')
        api_key = data.get('api_key')
        secret_key = data.get('secret_key')
        
        if not all([exchange, api_key, secret_key]):
            return jsonify({
                "success": False,
                "message": "exchange, api_key, secret_key 필드가 필요합니다"
            }), 400
        
        # API 키 저장
        success = config_manager.save_api_keys(exchange, api_key, secret_key)
        
        if success:
            # 거래소 재초기화
            trading_engine.initialize_exchanges()
            
            return jsonify({
                "success": True,
                "message": f"{exchange} API 키가 저장되었습니다"
            })
        else:
            return jsonify({
                "success": False,
                "message": "API 키 저장에 실패했습니다"
            }), 500
    
    except Exception as e:
        logger.error(f"❌ API 키 저장 오류: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/test', methods=['POST'])
def test_signal():
    """시그널 테스트 (실제 거래 없이 검증만)"""
    try:
        signal = request.get_json()
        
        # 거래 비활성화 상태로 임시 변경
        original_state = config["trading"]["enable_trading"]
        config["trading"]["enable_trading"] = False
        
        # 시그널 검증
        result = trading_engine.execute_signal(signal)
        
        # 원래 상태로 복구
        config["trading"]["enable_trading"] = original_state
        
        return jsonify({
            "success": True,
            "message": "시그널 검증 완료 (실제 거래 없음)",
            "validation": result
        })
    
    except Exception as e:
        logger.error(f"❌ 시그널 테스트 오류: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == '__main__':
    # 로그 디렉토리 생성
    os.makedirs('/var/log/kjbot', exist_ok=True)
    
    # 서버 설정
    host = config["server"]["host"]
    port = config["server"]["port"]
    debug = config["server"]["debug"]
    
    logger.info(f"🚀 KJBot Webhook Server 시작")
    logger.info(f"📍 주소: http://{host}:{port}")
    logger.info(f"🔗 Webhook URL: http://<서버IP>:{port}/webhook")
    
    # 서버 실행
    app.run(host=host, port=port, debug=debug)
