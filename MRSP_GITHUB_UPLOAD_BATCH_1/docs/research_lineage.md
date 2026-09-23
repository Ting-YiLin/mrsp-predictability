# Research Lineage（研究谱系）

## 0. 研究问题如何收敛

这条研究线最终没有收敛到“最复杂、最高分的预测模型”，而是收敛到两个问题：

1. 家庭历史是否提供稳定、可复现的个体化信息？
2. 在预测结果发生前，能否识别“值得预测”的家庭×商品事件，并对难以预测的事件选择 ABSTAIN（放弃预测）？

## 1. V0.7–V0.8：识别早期伪信号

- V0.7：row-order state 曾产生很强结果，但缺可靠 timestamp，不能解释为真实时间状态。
- V0.8：发现 choice set 把不同品类热门商品混成 8 选 1；k>0 又从 market prior 机械切换为 uniform prior。
- 结论：先修“问题定义”和“先验连续性”，不能把漂亮分数当机制。

## 2. V0.9–V0.11：家庭历史成为主干，复杂机制被逐步削弱

- V0.9：改成同品类 substitute proxy，并真正实现 `market prior × lambda + household evidence`。家庭偏好在 Milk / White Bread / Wheat Bread 等竞争品类显著增强。
- V0.10：尝试 Market Uncertainty × Persistent Heterogeneity × Context Sensitivity 三轴；深审发现 H3 early group 含 k=0 的机械偏差、H4 缺必要 nested ablation。
- V0.11 / V0.11R1：H2 fixed-cohort 边界从 >=10 修成 >=11 post-reset events 后只剩 2 个合格集合，故 DATA_LIMITED；H4 pooled 正向由 H01 高度驱动且 leave-one-set-out 变号，故不支持“通用第三轴”。

## 3. Wave1：把问题从机制故事改成 Prediction Frontier（预测能力边界）

- 9 个主要六选一商品组、两个前向测试窗，共 17,408 事件。
- B0 市场先验约 37.28%，B1 家庭历史约 64.53%，B2 行为融合约 65.52%。
- 关键结构：家庭历史带来约 +27.25pp；B2 只比 B1 多约 +0.99pp。
- E2 首次显示“哪些事件好预测”本身可被学习：两个测试窗 AUROC 约 .724 / .712，最高与最低可预测四分位准确率相差约 46 / 44pp。

## 4. Wave2A / 2B：复杂路由与困难案例救援没有成为主线

- W2A realized-label oracle 有大上限，但实际 learned router 没有打败 B2。
- W2A simple confidence ranking 的 selective prediction 很强。
- W2B switch specialist / cold-start / hard-case rescue 没有形成稳定可部署改善。
- 结论：停止追逐复杂“每种情况不同模型”的路由。

## 5. PHCM / Rolling / Tournament / Confidence：确认“复杂度小增益 ≠ 实用升级”

- 商品×历史模型路由不稳定，且格子层 oracle 相对 B2 剩余空间很小。
- 多策略 tournament 中复杂策略没有稳定击败简单基准。
- 26,659 个有家庭历史事件中 B2 比 B1 高 +1.26pp，且 household/week bootstrap 都支持是真实增益；但低于预先定义 3pp 实用门槛，所以正式保留 B1 simple default。

## 6. Predictability Frontier：P1 家庭稳定度出现

冻结的简单 P1：

`maturity(k) = clip(log(1+k) / log(21), 0, 1)`

`core = 0.30*top_share + 0.25*(1-normalized_entropy) + 0.25*(1-switch_rate) + 0.20*recent_concentration`

`P1 = clip(maturity * core, 0, 1)`

在 9 商品开发集：P1 top20-bottom20 future accuracy gap 约 40.9pp；60% coverage accuracy 约 71.36%，全体约 62.30%。更复杂 P4 只有约 2.23pp 额外提升，因此未取代 P1。

## 7. Action Map：把“可预测”与“是否需要个体化”分开

系统动作收敛为：

- 市场本身已足够准 → B0；
- 家庭稳定、且家庭历史有实质价值 → B1；
- 否则 → ABSTAIN。

## 8. Generalization Batch 1：100 个新商品

- 从 CJ9 上游用 week<=22 metadata/support 重建 507 个合法候选。
- 固定规则选 100 个新商品组；600 个 SKU 全部唯一，且与旧开发商品零重叠。
- 99 个在 W3-W6 有后期事件；52,854 个评估事件。
- Frozen GLOBAL_P1_B1：39.16% coverage / 76.18% accuracy；21.49% / 83.55%；11.50% / 88.14%。

## 9. Confirmatory Batch 2：完全冻结后的第二批确认

- P1 公式、cutoff、B0/B1、时间窗全部冻结。
- Representative：100 selected / 99 evaluated，40,474 events。
- 41.08% / 77.17%；22.00% / 84.78%；11.01% / 90.06%。
- Department Challenge：100 selected / 99 evaluated，36,027 events；在 60-target cutoff 下 40.22% coverage / 79.33% accuracy，B1-all=61.18%。7 个有足够商品数的部门中 6 个通过预设 >=10pp gain 标准；Produce 为 +8.62pp，方向仍正但未达门槛。

## 10. 当前冻结状态

- P1：**CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT**。
- 不再在同一面板继续优化 P1。
- 尚未完成：外部零售商／外部消费者面板验证。
- 下一研究线若继续，应转向 Purchase Incidence（购买发生预测）→ Conditional Choice（条件式六选一），而不是继续榨 P1。
