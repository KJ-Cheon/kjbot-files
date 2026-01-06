"""
KJBot Configuration Manager
API 키 암호화 저장 및 설정 관리
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class ConfigManager:
    """설정 및 API 키 관리 클래스"""
    
    def __init__(self, config_dir: str = "/etc/kjbot"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.yaml"
        self.secrets_file = self.config_dir / "secrets.enc"
        
        # 디렉토리 생성
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 암호화 키 설정
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key:
            # 새 키 생성
            self.encryption_key = Fernet.generate_key().decode()
            print(f"⚠️  새 암호화 키 생성됨: {self.encryption_key}")
            print("   .env 파일에 ENCRYPTION_KEY로 저장하세요!")
        
        self.cipher = Fernet(self.encryption_key.encode())
    
    def save_api_keys(self, exchange: str, api_key: str, secret_key: str) -> Tuple[bool, str]:
        """
        API 키를 암호화하여 저장
        
        Args:
            exchange: 거래소 이름 (binance, upbit)
            api_key: API 키
            secret_key: Secret 키
        
        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            # 기존 secrets 로드
            secrets = self.load_secrets()
            
            # 새 키 추가
            secrets[exchange] = {
                "api_key": api_key,
                "secret_key": secret_key
            }
            
            # 암호화
            encrypted_data = self.cipher.encrypt(
                json.dumps(secrets).encode()
            )
            
            # 저장
            with open(self.secrets_file, "wb") as f:
                f.write(encrypted_data)
            
            # 파일 권한 설정 (Linux only)
            if os.name != 'nt':
                os.chmod(self.secrets_file, 0o600)
            
            print(f"✅ {exchange} API 키 저장 완료")
            return True, ""
            
        except Exception as e:
            error_msg = f"API 키 저장 실패: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def load_secrets(self) -> Dict[str, Dict[str, str]]:
        """암호화된 API 키 로드"""
        if not self.secrets_file.exists():
            return {}
        
        try:
            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            print(f"❌ API 키 로드 실패: {e}")
            return {}
    
    def get_api_keys(self, exchange: str) -> Optional[Dict[str, str]]:
        """특정 거래소의 API 키 조회"""
        secrets = self.load_secrets()
        return secrets.get(exchange)
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """일반 설정 저장 (YAML)"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            print(f"✅ 설정 저장 완료: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """일반 설정 로드 (기본값과 병합)"""
        default_config = self.get_default_config()
        
        if not self.config_file.exists():
            return default_config
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)
                if not loaded_config:
                    return default_config
                
                # 기본값과 병합 (누락된 섹션/필드 자동 추가)
                merged_config = default_config.copy()
                for section, values in loaded_config.items():
                    if isinstance(values, dict) and section in merged_config:
                        merged_config[section].update(values)
                    else:
                        merged_config[section] = values
                
                return merged_config
                
        except Exception as e:
            print(f"❌ 설정 로드 실패: {e}")
            return default_config
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "trading": {
                "default_exchange": "binance",
                "default_leverage": 1,
                "max_position_size": 100,  # 웹훅 누락 시 안전장치 금액
                "enable_trading": True,
                "margin_mode": "isolated"
            },
            "security": {
                "require_ip_whitelist": False,
                "allowed_ips": [],
                "level": "INFO",
                "file": "/var/log/kjbot/kjbot.log"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            }
        }
    
    def delete_api_keys(self, exchange: str) -> bool:
        """특정 거래소의 API 키 삭제"""
        try:
            secrets = self.load_secrets()
            if exchange in secrets:
                del secrets[exchange]
                
                # 재암호화 및 저장
                encrypted_data = self.cipher.encrypt(
                    json.dumps(secrets).encode()
                )
                
                with open(self.secrets_file, "wb") as f:
                    f.write(encrypted_data)
                
                print(f"✅ {exchange} API 키 삭제 완료")
                return True
            else:
                print(f"⚠️  {exchange} API 키가 존재하지 않습니다")
                return False
                
        except Exception as e:
            print(f"❌ API 키 삭제 실패: {e}")
            return False


# 싱글톤 인스턴스
config_manager = ConfigManager()


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 ConfigManager 테스트")
    
    # 설정 저장
    test_config = config_manager.get_default_config()
    config_manager.save_config(test_config)
    
    # 설정 로드
    loaded_config = config_manager.load_config()
    print(f"로드된 설정: {loaded_config}")
    
    # API 키 저장 (테스트)
    config_manager.save_api_keys(
        "binance",
        "test_api_key_123",
        "test_secret_key_456"
    )
    
    # API 키 로드
    keys = config_manager.get_api_keys("binance")
    print(f"로드된 API 키: {keys}")
