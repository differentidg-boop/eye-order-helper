"""從 SAP「Customer Master Report - Partner View」產生下單小幫手的客戶名單。
用法：python3 build_customers.py <主檔.xlsx> <optical_whitelist.json> <輸出.json>
規則：
- 排除 Deletion flag = X 的客戶（含其分店）
- Price List Type：BA → 藥局價、BB → 眼科價；BC（眼鏡行）只保留白名單內的
- Industry 4901 Drug Store → 門前藥局（BB）；3xxx → 藥局；其他 → 診所
- Ship-to 分店：總公司有 ≥3 家分店視為連鎖體系，品項全走直走價
"""
import sys, re, json
import pandas as pd

COLS = ['acct','acct_d','cust','name','group','street','sort','pf','pnum','pname','psort','pstreet','pgroup','tax','tax5','tel','cls','cls_d','ind','ind_d','plt','cpg','h3','h4','h5','x','pay','pay_d','clerk','inv','inv_d','block','del','n']
CHAIN_MIN = 3

def half(s):
    return ''.join(chr(ord(c)-0xFEE0) if 0xFF01 <= ord(c) <= 0xFF5E else c for c in str(s))

def area(street):
    s = half(street).replace('巿', '市')
    if s.startswith('台'): s = '臺' + s[1:]
    m = re.match(r'(.{2}[縣市])(.{1,3}?[區鄉鎮市])', s)
    if m: return m.group(1) + m.group(2)
    m = re.match(r'(.{2}[縣市])', s)
    return m.group(1) if m else ''

def ctype(ind, plt):
    if plt == 'BC': return 'optical'
    if ind == '4901': return 'door'
    if str(ind).startswith('3'): return 'pharm'
    return 'clinic'

def main(src, wl_path, out):
    df = pd.read_excel(src, 'DS_1', header=None, skiprows=3, dtype=str)
    df.columns = COLS[:df.shape[1]]
    df = df[df.acct.notna() & df.cust.notna()]
    cust = df.drop_duplicates('cust').set_index('cust')
    wl = set(json.load(open(wl_path, encoding='utf-8')))
    deleted = set(cust.index[cust['del'] == 'X'])
    ship = df[df.pf == 'Ship-to party']
    branches = ship[ship.pnum != ship.cust].groupby('cust').pnum.nunique()
    rows = {}
    for cid, r in cust.iterrows():
        if cid in deleted: continue
        plt = r.plt
        if plt not in ('BA', 'BB', 'BC'): continue
        if plt == 'BC' and r['name'] not in wl and not any(n in wl for n in ship[ship.cust == cid].pname):
            continue
        chain = int(branches.get(cid, 0)) >= CHAIN_MIN
        t = ctype(r.ind, plt)
        def add(num, name, street):
            if num in deleted or num in rows: return
            if plt == 'BC' and name not in wl: return
            rows[num] = [name, area(street), street, num, t, 1 if (chain and num != cid) else 0]
        add(cid, r['name'], r.street)
        for _, s in ship[ship.cust == cid].drop_duplicates('pnum').iterrows():
            add(s.pnum, s.pname, s.pstreet)
    data = sorted(rows.values(), key=lambda x: x[3])
    json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{len(data)} 筆客戶')

if __name__ == '__main__':
    main(*sys.argv[1:4])
