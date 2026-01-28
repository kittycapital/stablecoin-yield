#!/usr/bin/env python3
"""
스테이블코인 수익률 데이터 수집 스크립트
DeFiLlama API 사용 (무료, API 키 불필요)
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# ============================================
# 설정
# ============================================

DEFILLAMA_API = "https://yields.llama.fi/pools"

# 대상 스테이블코인
STABLECOINS = ["USDC", "USDT", "DAI", "USDe", "PYUSD"]

# 대상 체인
CHAINS = ["Ethereum", "Solana", "Arbitrum", "Optimism", "BSC", "Base", "Polygon", "Avalanche"]

# 체인 이름 매핑 (표시용)
CHAIN_NAMES = {
    "Ethereum": "Ethereum",
    "Solana": "Solana",
    "Arbitrum": "Arbitrum",
    "Optimism": "Optimism",
    "BSC": "BNB Chain",
    "Base": "Base",
    "Polygon": "Polygon",
    "Avalanche": "Avalanche"
}

# 최소 TVL ($100K)
MIN_TVL = 100000


def fetch_yields():
    """DeFiLlama에서 수익률 데이터 가져오기"""
    print("📡 DeFiLlama API 호출 중...")
    
    try:
        response = requests.get(DEFILLAMA_API, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        pools = data.get("data", [])
        print(f"✅ 총 {len(pools)}개 풀 데이터 수신")
        
        return pools
        
    except Exception as e:
        print(f"❌ API 오류: {e}")
        return []


def filter_pools(pools):
    """스테이블코인, 체인, TVL 필터링"""
    filtered = []
    
    for pool in pools:
        # 체인 확인
        chain = pool.get("chain", "")
        if chain not in CHAINS:
            continue
        
        # 심볼 확인 (스테이블코인)
        symbol = pool.get("symbol", "")
        
        # 스테이블코인인지 확인
        matched_stable = None
        for stable in STABLECOINS:
            if stable.upper() in symbol.upper():
                matched_stable = stable
                break
        
        if not matched_stable:
            continue
        
        # TVL 확인
        tvl = pool.get("tvlUsd", 0) or 0
        if tvl < MIN_TVL:
            continue
        
        # APY 확인
        apy = pool.get("apy", 0) or 0
        if apy <= 0 or apy > 1000:  # 비정상적인 APY 제외
            continue
        
        filtered.append({
            "protocol": pool.get("project", "Unknown"),
            "chain": CHAIN_NAMES.get(chain, chain),
            "symbol": matched_stable,
            "pool": symbol,
            "apy": round(apy, 2),
            "tvl": tvl,
            "apyBase": round(pool.get("apyBase", 0) or 0, 2),
            "apyReward": round(pool.get("apyReward", 0) or 0, 2),
        })
    
    # APY 높은 순으로 정렬
    filtered.sort(key=lambda x: x["apy"], reverse=True)
    
    print(f"✅ 필터링 후 {len(filtered)}개 풀")
    
    return filtered


def main():
    print("=" * 50)
    print("🚀 스테이블코인 수익률 데이터 수집 시작")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 데이터 가져오기
    pools = fetch_yields()
    
    if not pools:
        print("❌ 데이터를 가져올 수 없습니다")
        return
    
    # 필터링
    filtered = filter_pools(pools)
    
    # 결과 저장
    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "minTvl": MIN_TVL,
        "pools": filtered,
        "stablecoins": STABLECOINS,
        "chains": list(CHAIN_NAMES.values())
    }
    
    output_path = Path(__file__).parent.parent / "data" / "yields.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"✅ 완료! {len(filtered)}개 풀 저장됨")
    print(f"📁 {output_path}")
    print("=" * 50)
    
    # 상위 10개 출력
    print("\n📊 상위 10개 APY:")
    for i, pool in enumerate(filtered[:10], 1):
        print(f"  {i}. {pool['protocol']:15} {pool['chain']:10} {pool['symbol']:6} {pool['apy']:6.2f}% ${pool['tvl']/1e6:.1f}M")


if __name__ == "__main__":
    main()
