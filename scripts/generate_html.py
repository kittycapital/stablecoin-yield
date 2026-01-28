#!/usr/bin/env python3
"""
JSON 데이터를 읽어서 대시보드 HTML 생성
"""

import json
from pathlib import Path

def generate_html():
    # 데이터 로드
    data_path = Path(__file__).parent.parent / "data" / "yields.json"
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    last_updated = data["lastUpdated"]
    min_tvl = data["minTvl"]
    pools_json = json.dumps(data["pools"], ensure_ascii=False)
    stablecoins_json = json.dumps(data["stablecoins"], ensure_ascii=False)
    chains_json = json.dumps(data["chains"], ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>스테이블코인 수익률 대시보드</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: #000; 
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        
        .header {{ 
            margin-bottom: 24px;
        }}
        .title {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; }}
        .subtitle {{ font-size: 13px; color: #6b7280; }}
        .subtitle span {{ color: #9ca3af; }}
        
        .filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 24px;
            margin-bottom: 24px;
            padding: 20px;
            background: #111;
            border-radius: 12px;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .filter-label {{
            font-size: 12px;
            color: #6b7280;
            font-weight: 500;
        }}
        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .filter-btn {{
            padding: 6px 12px;
            border: 1px solid #333;
            background: transparent;
            color: #9ca3af;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        .filter-btn:hover {{ border-color: #555; color: #fff; }}
        .filter-btn.active {{ 
            background: #3b82f6; 
            border-color: #3b82f6; 
            color: #fff; 
        }}
        
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: #111;
            border-radius: 10px;
            padding: 16px;
        }}
        .stat-label {{ font-size: 12px; color: #6b7280; margin-bottom: 4px; }}
        .stat-value {{ font-size: 24px; font-weight: 700; color: #22c55e; }}
        .stat-value.neutral {{ color: #fff; }}
        
        .table-container {{
            background: #111;
            border-radius: 12px;
            overflow: hidden;
        }}
        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #222;
        }}
        .table-title {{ font-size: 14px; font-weight: 600; }}
        .table-count {{ font-size: 12px; color: #6b7280; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 12px 16px;
            font-size: 11px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            border-bottom: 1px solid #222;
            cursor: pointer;
            transition: color 0.2s;
        }}
        th:hover {{ color: #fff; }}
        th.sorted {{ color: #3b82f6; }}
        td {{
            padding: 14px 16px;
            font-size: 13px;
            border-bottom: 1px solid #1a1a1a;
        }}
        tr:hover {{ background: #0a0a0a; }}
        
        .protocol-cell {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .protocol-icon {{
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: #222;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
        }}
        .protocol-name {{ font-weight: 500; }}
        
        .chain-badge {{
            display: inline-block;
            padding: 4px 8px;
            background: #1a1a1a;
            border-radius: 4px;
            font-size: 11px;
            color: #9ca3af;
        }}
        
        .stable-badge {{
            display: inline-block;
            padding: 4px 8px;
            background: #1e3a5f;
            border-radius: 4px;
            font-size: 11px;
            color: #60a5fa;
            font-weight: 500;
        }}
        
        .apy-value {{
            font-weight: 700;
            color: #22c55e;
            font-size: 15px;
        }}
        
        .tvl-value {{
            color: #d1d5db;
        }}
        
        .empty-state {{
            padding: 60px 20px;
            text-align: center;
            color: #6b7280;
        }}
        
        @media (max-width: 768px) {{
            .filters {{ flex-direction: column; gap: 16px; }}
            th, td {{ padding: 10px 12px; font-size: 12px; }}
            .protocol-icon {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">💰 스테이블코인 수익률 대시보드</h1>
            <p class="subtitle">
                마지막 업데이트: {last_updated} · 
                <span>TVL ${min_tvl/1000:.0f}K 이상 · DeFiLlama 데이터</span>
            </p>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <div class="filter-label">스테이블코인</div>
                <div class="filter-buttons" id="stable-filters">
                    <button class="filter-btn active" data-filter="all">전체</button>
                </div>
            </div>
            <div class="filter-group">
                <div class="filter-label">체인</div>
                <div class="filter-buttons" id="chain-filters">
                    <button class="filter-btn active" data-filter="all">전체</button>
                </div>
            </div>
        </div>
        
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-label">최고 APY</div>
                <div class="stat-value" id="stat-max-apy">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">평균 APY</div>
                <div class="stat-value" id="stat-avg-apy">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">표시된 풀</div>
                <div class="stat-value neutral" id="stat-pool-count">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">총 TVL</div>
                <div class="stat-value neutral" id="stat-total-tvl">-</div>
            </div>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <div class="table-title">수익률 순위</div>
                <div class="table-count" id="table-count">0개 풀</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th data-sort="protocol">프로토콜</th>
                        <th data-sort="chain">체인</th>
                        <th data-sort="symbol">스테이블코인</th>
                        <th data-sort="apy" class="sorted">APY ↓</th>
                        <th data-sort="tvl">TVL</th>
                    </tr>
                </thead>
                <tbody id="table-body">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const POOLS = {pools_json};
        const STABLECOINS = {stablecoins_json};
        const CHAINS = {chains_json};
        
        let currentStableFilter = 'all';
        let currentChainFilter = 'all';
        let currentSort = {{ field: 'apy', desc: true }};
        
        // 필터 버튼 생성
        function initFilters() {{
            const stableContainer = document.getElementById('stable-filters');
            STABLECOINS.forEach(stable => {{
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filter = stable;
                btn.textContent = stable;
                stableContainer.appendChild(btn);
            }});
            
            const chainContainer = document.getElementById('chain-filters');
            CHAINS.forEach(chain => {{
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filter = chain;
                btn.textContent = chain;
                chainContainer.appendChild(btn);
            }});
            
            // 이벤트 리스너
            stableContainer.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    stableContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentStableFilter = btn.dataset.filter;
                    renderTable();
                }});
            }});
            
            chainContainer.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    chainContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentChainFilter = btn.dataset.filter;
                    renderTable();
                }});
            }});
        }}
        
        // 정렬 이벤트
        function initSort() {{
            document.querySelectorAll('th[data-sort]').forEach(th => {{
                th.addEventListener('click', () => {{
                    const field = th.dataset.sort;
                    if (currentSort.field === field) {{
                        currentSort.desc = !currentSort.desc;
                    }} else {{
                        currentSort.field = field;
                        currentSort.desc = true;
                    }}
                    
                    document.querySelectorAll('th').forEach(t => {{
                        t.classList.remove('sorted');
                        t.textContent = t.textContent.replace(' ↓', '').replace(' ↑', '');
                    }});
                    th.classList.add('sorted');
                    th.textContent += currentSort.desc ? ' ↓' : ' ↑';
                    
                    renderTable();
                }});
            }});
        }}
        
        // 테이블 렌더링
        function renderTable() {{
            let filtered = POOLS.filter(pool => {{
                if (currentStableFilter !== 'all' && pool.symbol !== currentStableFilter) return false;
                if (currentChainFilter !== 'all' && pool.chain !== currentChainFilter) return false;
                return true;
            }});
            
            // 정렬
            filtered.sort((a, b) => {{
                let aVal = a[currentSort.field];
                let bVal = b[currentSort.field];
                if (typeof aVal === 'string') {{
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                }}
                if (currentSort.desc) {{
                    return bVal > aVal ? 1 : -1;
                }} else {{
                    return aVal > bVal ? 1 : -1;
                }}
            }});
            
            // 통계 업데이트
            updateStats(filtered);
            
            // 테이블 렌더링
            const tbody = document.getElementById('table-body');
            
            if (filtered.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" class="empty-state">조건에 맞는 풀이 없습니다</td></tr>';
                document.getElementById('table-count').textContent = '0개 풀';
                return;
            }}
            
            document.getElementById('table-count').textContent = `${{filtered.length}}개 풀`;
            
            tbody.innerHTML = filtered.map(pool => `
                <tr>
                    <td>
                        <div class="protocol-cell">
                            <div class="protocol-icon">${{pool.protocol.substring(0, 2).toUpperCase()}}</div>
                            <span class="protocol-name">${{pool.protocol}}</span>
                        </div>
                    </td>
                    <td><span class="chain-badge">${{pool.chain}}</span></td>
                    <td><span class="stable-badge">${{pool.symbol}}</span></td>
                    <td><span class="apy-value">${{pool.apy.toFixed(2)}}%</span></td>
                    <td><span class="tvl-value">${{formatTvl(pool.tvl)}}</span></td>
                </tr>
            `).join('');
        }}
        
        // TVL 포맷
        function formatTvl(tvl) {{
            if (tvl >= 1e9) return `$` + (tvl / 1e9).toFixed(2) + `B`;
            if (tvl >= 1e6) return `$` + (tvl / 1e6).toFixed(2) + `M`;
            if (tvl >= 1e3) return `$` + (tvl / 1e3).toFixed(0) + `K`;
            return `$` + tvl.toFixed(0);
        }}
        
        // 통계 업데이트
        function updateStats(pools) {{
            if (pools.length === 0) {{
                document.getElementById('stat-max-apy').textContent = '-';
                document.getElementById('stat-avg-apy').textContent = '-';
                document.getElementById('stat-pool-count').textContent = '0';
                document.getElementById('stat-total-tvl').textContent = '-';
                return;
            }}
            
            const maxApy = Math.max(...pools.map(p => p.apy));
            const avgApy = pools.reduce((sum, p) => sum + p.apy, 0) / pools.length;
            const totalTvl = pools.reduce((sum, p) => sum + p.tvl, 0);
            
            document.getElementById('stat-max-apy').textContent = maxApy.toFixed(2) + '%';
            document.getElementById('stat-avg-apy').textContent = avgApy.toFixed(2) + '%';
            document.getElementById('stat-pool-count').textContent = pools.length;
            document.getElementById('stat-total-tvl').textContent = formatTvl(totalTvl);
        }}
        
        // 초기화
        initFilters();
        initSort();
        renderTable();
    </script>
</body>
</html>'''
    
    output_path = Path(__file__).parent.parent / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ HTML 생성 완료: {output_path}")


if __name__ == "__main__":
    generate_html()
