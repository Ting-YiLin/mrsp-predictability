# 方法

## 預測單位

每一列是一個固定六 SKU choice set（選擇集合）內的購買事件，`y∈{0,…,5}` 代表實際選擇的 SKU 索引。所有特徵都必須先建立，再用當前事件更新狀態，因此當期答案不能進入當期特徵。

## B0 市場先驗

```text
other_count_j = max(global_count_j_before_t - household_count_hj_before_t, 0) + 1
B0_j = other_count_j / Σ_l other_count_l
```

B0 明確扣掉目前家庭自己的歷史計數。

## B1 家庭歷史

```text
x_j  = lambda_bin * B0_j + household_count_hj_before_t
B1_j = x_j / Σ_l x_l
```

`lambda_bin` 只在過去 FIT/TUNE 區段選擇，歷史成熟度粗分 `0–2 / 3–9 / 10+`。

## B2 行為融合（只保留作開發比較）

B2 從 B1 機率出發，再加入上一選擇、repeat streak（重複連續度）、近期選擇份額、距離上次選擇時間等近期行為 offset（偏移）特徵。它有小幅增益，但沒有成為公開預設模型。

## P1 家庭穩定度

```text
maturity(k) = clip(log(1+k)/log(21), 0, 1)
core = 0.30*top_share + 0.25*(1-normalized_entropy) + 0.25*(1-switch_rate) + 0.20*recent_concentration
P1 = clip(maturity * core, 0, 1)
```

- `top_share`：家庭在此商品組歷史中最高候選份額；
- `normalized_entropy`：`-Σ p_j log(p_j)/log(6)`；
- `switch_rate`：相鄰歷史購買中切換 SKU 的比例；
- `recent_concentration`：最近最多5次選擇的最高份額；
- `k`：當前事件以前，在此 choice set 的累積購買次數。

## 凍結工作點

| 標籤 | P1 cutoff | 歷史校準覆蓋率 | 歷史校準準確率 |
|---|---:|---:|---:|
| 0.60 | 0.3608488067 | 64.07% | 69.06% |
| 0.70 | 0.5231119438 | 40.00% | 76.96% |
| 0.80 | 0.6660270792 | 20.01% | 86.93% |

標籤不是未來準確率保證，只是凍結工作點名稱。

## Walk-forward（逐段前向）

| 區塊 | FIT 到 | TUNE | EVAL |
|---|---:|---|---|
| W1 | 17 | 18–22 | 23–27 |
| W2 | 22 | 23–27 | 28–32 |
| W3 | 27 | 28–32 | 33–37 |
| W4 | 32 | 33–37 | 38–42 |
| W5 | 37 | 38–42 | 43–47 |
| W6 | 42 | 43–47 | 48–53 |

新商品確認證據使用 W3–W6。

## 新商品母體與結果盲化

候選商品組只使用 week 1–22：依 `product_type` 分組、取前6個支持度最高商品、只保留單商品 basket（購物籃）事件、要求至少120事件與25家庭、排除舊開發組與 GAS/FUEL、去除重複／高重疊組，再產生 stable hash（穩定雜湊）。得到507個合法候選。

第一批100商品先凍結。第二批確認包先重建這100個 stable key 並排除，再以完全不同的固定規則選 representative（代表樣本）與 department challenge（跨部門壓力樣本）；W3–W6 結果不得參與選樣。

## 主要選擇性政策

```text
P1 >= cutoff → 使用 B1 預測
P1 <  cutoff → ABSTAIN
```

`Coverage = 被接受事件 / 全部可評估事件`。

`Accuracy = 被接受事件中的正確預測 / 被接受事件`。
