# 眼科下單小幫手

團隊內部用的下單頁面（已加密）。選客戶 → 物流 → 通路 → 品項與搭贈，一鍵開 Outlook 新信。

- `index.html`：StaticRypt 加密後的頁面，需密碼或含密碼的分享連結才能解開。
- `.staticrypt.json`：加密用的 salt，更新頁面時沿用，分享連結才不會變。

## 每月更新客戶名單

1. 取得 SAP「Customer Master Report - Partner View」原始檔（不用整理）。
2. `python3 tools/build_customers.py 主檔.xlsx tools/optical_whitelist.json customers.json`
3. 把 customers.json 嵌入頁面後，用同一組 `.staticrypt.json` 重新加密，連結不變。

分類規則寫在 `tools/build_customers.py` 開頭；要保留的眼鏡行列在 `tools/optical_whitelist.json`。
