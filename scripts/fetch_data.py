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
KNOWN_STABLECOINS = {
    "USDC", "USDT", "DAI", "USDE", "PYUSD",
    "USDC.E", "USDT.E", "USDBC", "AXLUSDC", "AXLUSDT",
    "MUSDC", "MUSDT", "WUSDC", "SUSDC", "SUSDT",
    "SDAI", "EDAI",
    "AUSDC", "AUSDT", "ADAI", "AETHUSDC", "AETHUSDT", "AETHDAI",
    "AVUSDC", "AVUSDT", "AVDAI",
    "CUSDC", "CDAI", "CUSDT",
    "FRAX", "TUSD", "BUSD", "LUSD", "GUSD", "SUSD",
    "CRVUSD", "GHO", "USDD", "FDUSD", "USDP", "USDS",
    "DOLA", "MIM", "ALUSD", "USP", "HAY", "CUSD", "AUSD",
    "USDB", "USD+", "USDX", "EUSD", "ZUSD", "MUSD", "HUSD",
    "OUSD", "USDM", "USDK", "RSV", "RUSD", "USDN", "PUSD",
    "DUSD", "USDA", "XUSD", "YUSD", "IUSD",
    "MSUSD", "MKUSD", "STUSD", "SFRAX", "SUSDE", "EURA",
    "EURS", "EURT", "JEUR", "AGEUR", "EUROC",
    "SUSDL", "USDR", "USDL", "FUSDC", "FUSDT",
    "YDAI", "YUSDC", "YUSDT",
    "IDAI", "IUSDC", "IUSDT",
    "BDAI", "BUSDC", "BUSDT",
    "REUSDC", "REUSDT", "REUSDE", "REDAI",
    "AAVEGHO", "AAVEUSDC", "AAVEUSDT",
    "USDFL", "USDF", "USDY",
}

# 검증된 프로토콜 화이트리스트
PROTOCOL_WHITELIST = {
    # Lending
    "aave-v3", "aave-v2", "compound-v3", "compound-v2", "morpho",
    "morpho-blue", "morpho-aavev3", "spark",
    # DEX / AMM
    "curve-dex", "curve", "convex-finance", "uniswap-v3",
    "balancer-v2", "balancer-v3", "aerodrome-slipstream", "aerodrome",
    "velodrome-v2", "pancakeswap-amm-v3",
    # Yield
    "yearn-finance", "pendle", "beefy", "sommelier",
    "stake-dao", "concentrator", "stakedao",
    # Stablecoin native
    "makerdao", "maker", "sky", "ethena", "frax-lend", "liquity",
    # Other major
    "stargate", "fluid", "gearbox", "notional-v3",
    "angle", "origin-dollar", "mountain-protocol",
    "resolv", "usual", "euler", "euler-v2",
    "venus", "benqi", "radiant-v2",
    "seamless-protocol", "moonwell",
}

# 대상 체인
CHAINS = ["Ethereum", "Solana", "Arbitrum", "Optimism", "BSC", "Base", "Polygon", "Avalanche"]

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

# 최소 TVL ($1M)
MIN_TVL = 1_000_000

# 코인별 최대 풀 수
MAX_POOLS_PER_COIN = 15


def is_stablecoin_only_pool(symbol):
    """풀 심볼의 모든 토큰이 스테이블코인인지 확인"""
    tokens = re.split(r'[-/]', symbol.upper().strip())
    tokens = [t.strip() for t in tokens if t.strip()]

    if not tokens:
        return False

    for token in tokens:
        if token in KNOWN_STABLECOINS:
            continue
        matched = False
        for stable in sorted(KNOWN_STABLECOINS, key=len, reverse=True):
            if token.endswith(stable) and len(token) > len(stable):
                matched = True
                break
            if token.startswith(stable) and len(token) > len(stable):
                suffix = token[len(stable):]
                if re.match(r'^(V\d+|CORE|ENHANCED|CONS|TERM|TURBO|VAULT|RESERVOIR)$', suffix):
                    matched = True
                    break
        if not matched:
            return False

    return True


def fetch_yields():
    """DeFiLlama에서 수익률 데이터 가져오기"""
    print("DeFiLlama API 호출 중...")

    try:
        response = requests.get(DEFILLAMA_API, timeout=30)
        response.raise_for_status()
        data = response.json()

        pools = data.get("data", [])
        print(f"총 {len(pools)}개 풀 데이터 수신")

        return pools

    except Exception as e:
        print(f"API 오류: {e}")
        return []


def filter_pools(pools):
    """스테이블코인-스테이블코인 풀만 필터링 (화이트리스트 + TVL $1M+)"""
    filtered = []
    skipped_non_stable = 0
    skipped_protocol = 0

    for pool in pools:
        chain = pool.get("chain", "")
        if chain not in CHAINS:
            continue

        symbol = pool.get("symbol", "")
        protocol = pool.get("project", "").lower()

        # 프로토콜 화이트리스트 확인
        if protocol not in PROTOCOL_WHITELIST:
            skipped_protocol += 1
            continue

        # 스테이블코인 전용 풀 확인
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

        # TVL 확인 ($1M 이상)
        tvl = pool.get("tvlUsd", 0) or 0
        if tvl < MIN_TVL:
            continue

        # APY 확인
        apy = pool.get("apy", 0) or 0
        if apy <= 0 or apy > 1000:
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
            "isStablecoinPool": pool.get("stablecoin", False),
        })

    # APY 높은 순으로 정렬
    filtered.sort(key=lambda x: x["apy"], reverse=True)

    print(f"프로토콜 화이트리스트 외 제외: {skipped_protocol}개")
    print(f"비스테이블코인 혼합 풀 제외: {skipped_non_stable}개")
    print(f"필터 후 스테이블코인 전용 풀: {len(filtered)}개")

    # 코인별 상위 N개만 유지
    final = []
    coin_counts = {}
    for pool in filtered:
        coin = pool["symbol"]
        coin_counts[coin] = coin_counts.get(coin, 0) + 1
        if coin_counts[coin] <= MAX_POOLS_PER_COIN:
            final.append(pool)

    # 최종 APY 순 정렬
    final.sort(key=lambda x: x["apy"], reverse=True)

    print(f"코인별 상위 {MAX_POOLS_PER_COIN}개 적용 후: {len(final)}개")

    return final


def main():
    print("=" * 50)
    print("스테이블코인 수익률 데이터 수집 시작")
    print(f"TVL >= $1M | 검증된 프로토콜만 | 코인별 상위 {MAX_POOLS_PER_COIN}개")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    pools = fetch_yields()

    if not pools:
        print("데이터를 가져올 수 없습니다")
        return

    filtered = filter_pools(pools)

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

    print(f"\n{'=' * 50}")
    print(f"완료! {len(filtered)}개 풀 저장됨")
    print(f"{output_path}")
    print("=" * 50)

    print(f"\n상위 10개 APY:")
    for i, pool in enumerate(filtered[:10], 1):
        print(f"  {i}. {pool['protocol']:15} {pool['chain']:10} {pool['pool']:20} {pool['apy']:6.2f}% ${pool['tvl']/1e6:.1f}M")


if __name__ == "__main__":
    main()
