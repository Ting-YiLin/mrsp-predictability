# 第三方復現

## A. 沒有原始資料：驗證公開機器輸出

```bash
python reproduce/verify_release.py
```

它會從發布包中的正式 machine summary（機器摘要）重新讀取核心數值，與 `EXPECTED_RESULTS.json` 比對。

## B. 有相同 canonical CJ9：完整重跑

```bash
python -m pip install -r requirements.txt
python reproduce/run_full_reproduction.py --cj9 /path/to/CJ9
```

Windows：

```bat
reproduce\run_all.bat C:\path\to\CJ9
```

完整重跑會：重新雜湊資料 → 用 week≤22 重建候選母體 → 精確重建第一批100 stable keys → 排除第一批 → 固定規則建立第二批代表樣本與跨部門樣本 → W1–W6 → B0/B1/P1 → 產生確認分級 → 與公開 Expected Results（預期結果）比對。

核心 Coverage／Accuracy 允許絕對誤差 0.001（0.1 個百分點）；商品數、事件數與 confirmation grade（確認分級）要求精確一致。
