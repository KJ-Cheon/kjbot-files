import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom/client';
import './app.css';

// 타입 정의
interface Config {
    trading: {
        default_leverage: number;
        max_position_size: number;
        enable_trading: boolean;
        default_exchange: string;
        margin_mode: string;
    };
    security: {
        require_ip_whitelist: boolean;
        allowed_ips_count: number;
    };
    api_keys_status?: {
        [key: string]: boolean;
    };
}

interface TestState {
    action: string;
    symbol: string;
    leverage: number;
    amount: number;
    percent: number;
}

// 메인 앱 컴포넌트
const App: React.FC = () => {
    const [activeTab, setActiveTab] = useState<string>('dashboard');
    const [config, setConfig] = useState<Config | null>(null);
    const [message, setMessage] = useState<{ type: string; text: string } | null>(null);

    // API 설정 상태
    const [apiExchange, setApiExchange] = useState<string>('binance');
    const [apiKey, setApiKey] = useState<string>('');
    const [secretKey, setSecretKey] = useState<string>('');

    // 거래 설정 상태
    const [defaultLeverage, setDefaultLeverage] = useState<number>(1);
    const [maxPosition, setMaxPosition] = useState<number>(100); // 기본값 100
    const [enableTrading, setEnableTrading] = useState<boolean>(true);
    const [marginMode, setMarginMode] = useState<string>('isolated');

    // 테스트 상태
    const [testState, setTestState] = useState<TestState>({
        action: 'long_entry',
        symbol: 'BTCUSDT',
        leverage: 10,
        amount: 100,
        percent: 50
    });

    // API Base URL (상대 경로 - Nginx Reverse Proxy 사용)
    const getApiUrl = (path: string) => path;

    const showMessage = (type: string, text: string) => {
        setMessage({ type, text });
        setTimeout(() => setMessage(null), 5000);
    };

    const getServerIP = () => {
        return window.location.hostname;
    };

    // 설정 로드
    const loadConfig = useCallback(async () => {
        try {
            const response = await fetch(getApiUrl('/api/config'));
            const data = await response.json();
            if (data.success) {
                setConfig(data.config);
                // 안전장치 설정 로드
                setDefaultLeverage(data.config.trading.default_leverage || 1);
                setMaxPosition(data.config.trading.max_position_size || 100);
                setEnableTrading(data.config.trading.enable_trading);
                setMarginMode(data.config.trading.margin_mode || 'isolated');
            }
        } catch (error) {
            console.error('설정 로드 실패:', error);
        }
    }, []);

    useEffect(() => {
        loadConfig();
    }, [loadConfig]);

    // API 키 저장
    const handleSaveApiKeys = async () => {
        if (!apiKey || !secretKey) {
            showMessage('error', '❌ API Key와 Secret Key를 모두 입력하세요');
            return;
        }

        try {
            const response = await fetch(getApiUrl('/api/keys'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exchange: apiExchange,
                    api_key: apiKey,
                    secret_key: secretKey
                })
            });
            const data = await response.json();
            showMessage(data.success ? 'success' : 'error', data.success ? '✅ ' + data.message : '❌ ' + data.message);
            if (data.success) {
                setApiKey('');
                setSecretKey('');
            }
        } catch (error) {
            showMessage('error', '❌ 저장 실패: ' + (error as Error).message);
        }
    };

    // 거래 설정 저장
    const handleSaveTrading = async () => {
        try {
            const newConfig = {
                trading: {
                    default_leverage: defaultLeverage,
                    max_position_size: maxPosition,
                    enable_trading: enableTrading,
                    default_exchange: 'binance',
                    margin_mode: marginMode
                }
            };

            const response = await fetch(getApiUrl('/api/config'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            const data = await response.json();
            showMessage(data.success ? 'success' : 'error', data.success ? '✅ ' + data.message : '❌ ' + data.message);
            if (data.success) {
                loadConfig();
            }
        } catch (error) {
            showMessage('error', '❌ 저장 실패: ' + (error as Error).message);
        }
    };

    // 시그널 테스트
    const handleTestSignal = async () => {
        try {
            const signal: Record<string, string | number> = {
                action: testState.action,
                symbol: testState.symbol,
                leverage: testState.leverage,
                amount: testState.amount
            };

            if (testState.action.includes('exit')) {
                signal.percent = testState.percent;
            }

            const response = await fetch(getApiUrl('/api/test'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(signal)
            });
            const data = await response.json();
            showMessage(data.success ? 'success' : 'error', data.success ? '✅ ' + data.message : '❌ ' + data.message);
        } catch (error) {
            showMessage('error', '❌ 테스트 실패: ' + (error as Error).message);
        }
    };

    return (
        <div className="app">
            <header className="header">
                <h1>🤖 KJBOT</h1>
                <p>트레이딩뷰 웹훅봇</p>
            </header>

            <div className="tabs">
                <button
                    className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
                    onClick={() => setActiveTab('dashboard')}
                >
                    📊 대시보드
                </button>
                <button
                    className={`tab ${activeTab === 'api' ? 'active' : ''}`}
                    onClick={() => setActiveTab('api')}
                >
                    🔑 API 설정
                </button>
                <button
                    className={`tab ${activeTab === 'trading' ? 'active' : ''}`}
                    onClick={() => setActiveTab('trading')}
                >
                    ⚙️ 거래 설정
                </button>
                <button
                    className={`tab ${activeTab === 'test' ? 'active' : ''}`}
                    onClick={() => setActiveTab('test')}
                >
                    🧪 시그널 테스트
                </button>
            </div>

            <div className="container">
                {message && (
                    <div className={`message ${message.type}`}>
                        {message.text}
                    </div>
                )}

                {/* 대시보드 탭 */}
                {activeTab === 'dashboard' && (
                    <div className="tab-content">
                        <div className="card">
                            <h2>📊 시스템 상태</h2>
                            <div className="status-grid">
                                <div className="status-item">
                                    <span className="label">거래 설정:</span>
                                    <span className={`value ${config?.trading.enable_trading ? 'success' : 'error'}`}>
                                        {config?.trading.enable_trading ? '✅ 활성화' : '❌ 비활성화'}
                                    </span>
                                </div>
                                <div className="status-item">
                                    <span className="label">기본 거래소:</span>
                                    <span className="value">{config?.trading.default_exchange || 'binance'}</span>
                                </div>
                                <div className="status-item">
                                    <span className="label">메시지 수신:</span>
                                    <span className="value">{config?.security.require_ip_whitelist ? '보안모드' : '일반모드'}</span>
                                </div>
                            </div>
                            <button className="btn" onClick={loadConfig}>🔄 상태 새로고침</button>
                        </div>

                        <div className="card">
                            <h2>📝 웹훅 URL</h2>
                            <div className="info-box">
                                <code>http://{getServerIP()}/webhook</code>
                            </div>
                            <p className="hint">위의 URL을 트레이딩뷰 알림(얼러트)의 Webhook URL에 입력</p>
                        </div>
                    </div>
                )}

                {/* API 설정 탭 */}
                {activeTab === 'api' && (
                    <div className="tab-content">
                        <div className="card">
                            <h2>🔑 API 키 설정</h2>

                            {config && config.api_keys_status && config.api_keys_status[apiExchange] && (
                                <div style={{
                                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                    border: '1px solid #4caf50',
                                    color: '#4caf50',
                                    padding: '10px',
                                    borderRadius: '5px',
                                    marginBottom: '20px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px'
                                }}>
                                    <span>✅</span>
                                    <span><strong>{apiExchange}</strong> 키가 안전하게 등록되어 있습니다. (재입력 시 덮어쓰기)</span>
                                </div>
                            )}

                            <div className="form-group">
                                <label>거래소</label>
                                <select value={apiExchange} onChange={(e) => setApiExchange(e.target.value)}>
                                    <option value="binance">Binance (선물)</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>API Key</label>
                                <input
                                    type="text"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    placeholder="API Key 입력"
                                />
                            </div>

                            <div className="form-group">
                                <label>Secret Key</label>
                                <input
                                    type="password"
                                    value={secretKey}
                                    onChange={(e) => setSecretKey(e.target.value)}
                                    placeholder="Secret Key 입력"
                                />
                            </div>

                            <button className="btn" onClick={handleSaveApiKeys}>
                                💾 저장
                            </button>

                            <div className="info-box" style={{ marginTop: '20px' }}>
                                <h3>⚠️ 주의사항</h3>
                                <ul>
                                    <li>Binance API 권한: "Enable Futures(선물활성)" 필수</li>
                                    <li>출금(Withdrawal) 권한은 비활성화 권장</li>
                                    <li>보안을 위해 서버 IP를 트레이딩뷰 IP로 제한함</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                )}

                {/* 거래 설정 탭 */}
                {activeTab === 'trading' && (
                    <div className="tab-content">
                        <div className="card">
                            <h2>⚙️ 거래 안전장치 설정</h2>
                            <p className="hint" style={{ marginBottom: '20px' }}>트레이딩뷰 웹훅에서 값이 누락되었을 때 적용되는 기본값입니다.</p>

                            <div className="form-group">
                                <label>기본 레버리지 (x)</label>
                                <input
                                    type="number"
                                    value={defaultLeverage}
                                    onChange={(e) => setDefaultLeverage(Number(e.target.value))}
                                    min="1"
                                    max="125"
                                />
                                <p className="hint">⚠️ 웹훅 레버리지 전송 실패 시 적용되는 안전장치</p>
                            </div>

                            <div className="form-group">
                                <label>기본 진입 금액 (USDT)</label>
                                <input
                                    type="number"
                                    value={maxPosition}
                                    onChange={(e) => setMaxPosition(Number(e.target.value))}
                                    min="10"
                                />
                                <p className="hint">⚠️ 웹훅 포지션 크기 전송 실패 시 적용되는 안전장치</p>
                            </div>

                            <hr style={{ margin: '20px 0', border: '0', borderTop: '1px solid #333' }} />

                            <div className="form-group">
                                <label>마진 모드</label>
                                <select value={marginMode} onChange={(e) => setMarginMode(e.target.value)}>
                                    <option value="isolated">격리 마진 (Isolated)</option>
                                    <option value="cross">교차 마진 (Cross)</option>
                                </select>
                                <p className="hint">격리 마진: 각 포지션 독립 (안전/권장) | 교차 마진: 전체 잔고 공유</p>
                            </div>

                            <div className="form-group">
                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={enableTrading}
                                        onChange={(e) => setEnableTrading(e.target.checked)}
                                    />
                                    거래 시스템 활성화
                                </label>
                                <p className="hint">체크 해제 시 모든 거래 신호를 무시합니다 (긴급 정지)</p>
                            </div>

                            <button className="btn" onClick={handleSaveTrading}>
                                💾 설정 저장
                            </button>
                        </div>
                    </div>
                )}

                {/* 시그널 테스트 탭 */}
                {activeTab === 'test' && (
                    <div className="tab-content">
                        <div className="card">
                            <h2>🧪 시그널 테스트</h2>
                            <p className="hint">실제 거래 없이 시그널만 검증</p>

                            <div className="form-group">
                                <label>액션</label>
                                <select
                                    value={testState.action}
                                    onChange={(e) => setTestState({ ...testState, action: e.target.value })}
                                >
                                    <option value="long_entry">🟢 롱 진입</option>
                                    <option value="short_entry">🔴 숏 진입</option>
                                    <option value="long_exit">🟢 롱 청산</option>
                                    <option value="short_exit">🔴 숏 청산</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>심볼</label>
                                <input
                                    type="text"
                                    value={testState.symbol}
                                    onChange={(e) => setTestState({ ...testState, symbol: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>레버리지</label>
                                <input
                                    type="number"
                                    value={testState.leverage}
                                    onChange={(e) => setTestState({ ...testState, leverage: Number(e.target.value) })}
                                    min="1"
                                    max="125"
                                />
                            </div>

                            <div className="form-group">
                                <label>금액 (USDT)</label>
                                <input
                                    type="number"
                                    value={testState.amount}
                                    onChange={(e) => setTestState({ ...testState, amount: Number(e.target.value) })}
                                    min="10"
                                />
                            </div>

                            {testState.action.includes('exit') && (
                                <div className="form-group">
                                    <label>청산 비율 (%)</label>
                                    <input
                                        type="number"
                                        value={testState.percent}
                                        onChange={(e) => setTestState({ ...testState, percent: Number(e.target.value) })}
                                        min="1"
                                        max="100"
                                    />
                                </div>
                            )}

                            <button className="btn" onClick={handleTestSignal}>
                                🧪 테스트 실행
                            </button>

                            <div className="info-box" style={{ marginTop: '20px' }}>
                                <h3>📋 트레이딩뷰 웹훅URL</h3>
                                <code>http://{getServerIP()}/webhook</code>
                            </div>

                            <div className="info-box" style={{ marginTop: '20px' }}>
                                <h3>📋 메시지 형식 (JSON)</h3>
                                <p className="hint-small">수동테스트용 (실제 트레이딩뷰 얼러트 메세지는 비워야함)</p>
                                <pre>{JSON.stringify({
                                    action: testState.action,
                                    symbol: testState.symbol,
                                    leverage: testState.leverage,
                                    amount: testState.amount,
                                    ...(testState.action.includes('exit') && { percent: testState.percent })
                                }, null, 2)}</pre>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div >
    );
};

// 앱 마운트
const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(<App />);
