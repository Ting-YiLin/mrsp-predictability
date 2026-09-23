# Formula Authority（最终公式权威）

本文件只登记当前公开版本拟保留的冻结定义。所有数学式均由最终 Confirmatory Audit 的正式代码反向抽取。

## 1. 任务定义

每个事件已知属于一个固定的 6-alternative choice set（六候选选择集合）。目标变量 `y ∈ {0,...,5}` 是本次事件实际选择的 SKU 索引。所有特征必须在当前事件发生前构造。

## 2. B0 — Market Prior（市场先验）

对当前家庭 `h`、当前事件 `t`、候选商品 `j`：

`other_count_j = max(global_count_j_before_t - household_count_hj_before_t, 0) + 1`

`B0_j = other_count_j / Σ_l other_count_l`

因此 B0 明确排除当前家庭自己的历史计数，并加 1 平滑。

## 3. B1 — Household History（家庭历史）

`x_j = lambda_bin * B0_j + household_count_hj_before_t`

`B1_j = x_j / Σ_l x_l`

`lambda_bin` 依家庭在该 choice set 的预事件历史量粗分 `0–2 / 3–9 / 10+`，只使用过去 FIT/TUNE 区间选择；当前／未来事件不得参与。

## 4. P1 — Household Stability Predictability Score（家庭稳定度可预测性分数）

令 `k` 为该家庭在该 choice set 当前事件前的累计购买次数：

`maturity = clip(log(1+k) / log(21), 0, 1)`

其中：

- `top_share` = 家庭历史中最大候选份额；
- `normalized_entropy` = `-Σ p_j log(p_j) / log(6)`；
- `switch_rate` = 历史相邻购买选择发生切换的比例；
- `recent_concentration` = 最近最多 5 次购买中，最高候选份额。

冻结核心：

`core = 0.30*top_share + 0.25*(1-normalized_entropy) + 0.25*(1-switch_rate) + 0.20*recent_concentration`

`P1 = clip(maturity * core, 0, 1)`

没有学习参数、没有商品专属权重、没有使用当前标签。

## 5. Frozen P1 Cutoffs（冻结阈值）

由旧 9 商品历史区段校准后，在 Generalization 与 Confirmatory 阶段冻结：

| 目标标签 | P1 cutoff | 历史校准覆盖率 | 历史校准准确率 |
|---|---:|---:|---:|
| 0.60 | 0.3608488067 | 64.07% | 69.06% |
| 0.70 | 0.5231119438 | 40.00% | 76.96% |
| 0.80 | 0.6660270792 | 20.01% | 86.93% |
| 0.90 | 无冻结 cutoff | — | — |

注意：目标标签不是保证未来准确率等于 60/70/80%；它只是冻结 cutoff 的命名／校准目标。真正证据来自后续 untouched 批次实际表现。

## 6. Selective P1 Policy

对某目标 cutoff `c`：

- `P1 >= c` → 使用 B1 作答；
- `P1 < c` → ABSTAIN。

Accuracy 只在被接受事件上计算；Coverage = 被接受事件数 / 全部可评估事件数。

## 7. 代码权威路径

最终 Confirmatory Audit：

- `code/data.py`：严格 pre-event sequential feature construction；
- `code/models.py`：B1；
- `code/predictability.py`：P1；
- `code/run_confirmatory.py`：B0、walk-forward、policy evaluation；
- `cfg/frozen_p1_cutoffs.json`：冻结 cutoff；
- `cfg/study.json`：W1-W6、成功门槛与禁止事项。


## 8. Public source layout

Byte-level scientific authority is `reproduce/frozen_confirmatory/code/` plus its frozen `cfg/`. The top-level `src/` directory is a convenience mirror with import-path/public-path packaging adjustments only.
