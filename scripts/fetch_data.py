#!/usr/bin/env python3
"""
스테이블코인 수익률 데이터 수집 스크립트
DeFiLlama API 사용 (무료, API 키 불필요)
스테이블코인-스테이블코인 풀만 필터링 (L1/L2 토큰 혼합 풀 제외)
"""

import json
import re
import requests
from datetime import datetime
from pathlib import Path

# ============================================
# 설정
# ============================================

DEFILLAMA_API = "https://yields.llama.fi/pools"

# 대상 스테이블코인 (주요 추적 대상)
STABLECOINS = ["USDC", "USDT", "DAI", "USDe", "PYUSD"]

# 알려진 스테이블코인 목록 (풀 구성 검증용)
# 풀의 모든 토큰이 이 목록에 포함되어야 함
KNOWN_STABLECOINS = {
    # 주요 스테이블코인
    "USDC", "USDT", "DAI", "USDE", "PYUSD",
    # 변형 (브릿지/래핑)
    "USDC.E", "USDT.E", "USDBC", "AXLUSDC", "AXLUSDT",
    "MUSDC", "MUSDT", "WUSDC", "SUSDC", "SUSDT",
    "SDAI", "EDAI",
    # Aave 토큰 (이자 발생 스테이블)
    "AUSDC", "AUSDT", "ADAI", "AETHUSDC", "AETHUSDT", "AETHDAI",
    "AVUSDC", "AVUSDT", "AVDAI",
    # Compound 토큰
    "CUSDC", "CDAI", "CUSDT",
    # 기타 주요 스테이블코인
    "FRAX", "TUSD", "BUSD", "LUSD", "GUSD", "SUSD",
    "CRVUSD", "GHO", "USDD", "FDUSD", "USDP", "USDS",
    "DOLA", "MIM", "ALUSD", "USP", "HAY", "CUSD", "AUSD",
    "USDB", "USD+", "USDX", "EUSD", "ZUSD", "MUSD", "HUSD",
    "OUSD", "USDM", "USDK", "RSV", "RUSD", "USDN", "PUSD",
    "DUSD", "USDA", "XUSD", "YUSD", "IUSD",
    # 메타스테이블 / 합성
    "MSUSD", "MKUSD", "STUSD", "SFRAX", "SUSDE", "EURA",
    "EURS", "EURT", "JEUR", "AGEUR", "EUROC",
    "SUSDL", "USDR", "USDL", "FUSDC", "FUSDT",
    # DeFi 래핑 스테이블
    "YDAI", "YUSDC", "YUSDT",
    "IDAI", "IUSDC", "IUSDT",
    "BDAI", "BUSDC", "BUSDT",
    "REUSDC", "REUSDT", "REUSDE", "REDAI",
    # 기타
    "AAVEGHO", "AAVEUSDC", "AAVEUSDT",
    "USDFL", "USDF", "USDY",
}

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


def is_stablecoin_only_pool(symbol):
    """
    풀 심볼의 모든 토큰이 스테이블코인인지 확인
    예: "USDC-USDT" → True, "ETH-USDC" → False, "USDC" → True
    """
    # 구분자로 토큰 분리 (-, /)
    tokens = re.split(r'[-/]', symbol.upper().strip())
    tokens = [t.strip() for t in tokens if t.strip()]

    if not tokens:
        return False

    for token in tokens:
        # 정확히 매칭
        if token in KNOWN_STABLECOINS:
            continue
        # 부분 매칭 (프로토콜 접두사가 붙은 경우: e.g., "3FUSDC", "ALPHAUSDC")
        # 토큰 끝부분이 알려진 스테이블코인으로 끝나는지 확인
        matched = False
        for stable in sorted(KNOWN_STABLECOINS, key=len, reverse=True):
            if token.endswith(stable) and len(token) > len(stable):
                matched = True
                break
            # 접미사 패턴도 확인 (e.g., "USDCCORE", "USDCV2")
            if token.startswith(stable) and len(token) > len(stable):
                suffix = token[len(stable):]
                # 허용 접미사: 버전, vault 등
                if re.match(r'^(V\d+|CORE|ENHANCED|CONS|TERM|TURBO|VAULT|RESERVOIR)$', suffix):
                    matched = True
                    break
        if not matched:
            return False

    return True


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
    """스테이블코인-스테이블코인 풀만 필터링"""
    filtered = []
    skipped_non_stable = 0

    for pool in pools:
        # 체인 확인
        chain = pool.get("chain", "")
        if chain not in CHAINS:
            continue

        # 심볼 확인
        symbol = pool.get("symbol", "")

        # 1차: DeFiLlama stablecoin 플래그 확인
        is_stable_flag = pool.get("stablecoin", False)

        # 2차: 풀의 모든 토큰이 스테이블코인인지 확인
        if not is_stablecoin_only_pool(symbol):
            skipped_non_stable += 1
            continue

        # 주요 추적 대상 스테이블코인 매칭
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
            "isStablecoinPool": is_stable_flag,
        })

    # APY 높은 순으로 정렬
    filtered.sort(key=lambda x: x["apy"], reverse=True)

    print(f"🚫 비스테이블코인 혼합 풀 제외: {skipped_non_stable}개")
    print(f"✅ 스테이블코인 전용 풀: {len(filtered)}개")

    return filtered


def main():
    print("=" * 50)
    print("🚀 스테이블코인 수익률 데이터 수집 시작")
    print("📌 스테이블코인-스테이블코인 풀만 수집")
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
        print(f"  {i}. {pool['protocol']:15} {pool['chain']:10} {pool['pool']:20} {pool['apy']:6.2f}% ${pool['tvl']/1e6:.1f}M")


if __name__ == "__main__":
    main()
