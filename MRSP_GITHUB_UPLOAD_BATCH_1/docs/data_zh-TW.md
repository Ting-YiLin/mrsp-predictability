# 資料結構與公開狀態

完整復現需要 canonical `CJ9`（標準資料庫）：

```text
CJ9/
├── products.parquet（或 CSV 備用格式）
└── tx/
    ├── w01.parquet
    ├── ...
    └── w53.parquet
```

商品 metadata（中繼資料）至少需要 `product_id / product_type / department`。確認性 materializer（實體化程式）會使用家庭、basket、商品、week、transaction timestamp（交易時間）與銷售／折扣等欄位。

上游偵察曾記錄約146.9萬筆、weeks 1–53、2,469家庭、68,509商品的原始交易來源，之後由先前 builder（生成程式）轉成 CJ9。

目前 Release Candidate（發布候選版）**不包含逐筆原始消費資料**；在最終資料授權審計沒有閉環以前，GitHub 以「程式＋聚合結果＋雜湊＋重現說明」方式發布。
