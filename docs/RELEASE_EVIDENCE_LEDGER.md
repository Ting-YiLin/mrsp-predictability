# RELEASE_EVIDENCE_LEDGER（发布证据总账）

状态：**R1 EVIDENCE FREEZE CANDIDATE（第一轮证据冻结候选）**

本文件是后续 GitHub README、技术报告、图表与审计包的唯一数字来源候选。后续公开文本不得手工另抄未经本表登记的核心数字。

## 证据优先级

1. **CONFIRMATORY_PRIMARY / CONFIRMATORY_BREADTH**：第二批冻结确认，最高权威。
2. **GENERALIZATION_BATCH_1**：第一批新商品泛化，独立发现／复制证据。
3. **DEVELOPMENT**：9 商品开发阶段，只解释方法如何形成，不用于最终外推。
4. **NEGATIVE_DEVELOPMENT**：保留失败结果，防止事后包装。

## 登记证据

### E001 — DEVELOPMENT
**主张：** Household history is the dominant increment over a market-prior baseline in the original 9-product development panel.
**机器结果：** Pooled TEST_A+TEST_B across 17,408 events: B0=37.2817%, B1=64.5278%, B2=65.5216%; B1-B0=+27.2461pp; B2-B1=+0.9938pp.
**权威来源：** `W1_AUDIT` → `w/FULL/wave1_result.json -> assessment.aggregate_primary`
**状态：** `SUPPORTED_DEVELOPMENT`
**发布用途：** background / method evolution, not final generalization claim

### E002 — DEVELOPMENT
**主张：** Predictability differs strongly across events before the outcome, motivating selective prediction.
**机器结果：** Wave1 E2: TEST_A AUROC=0.7237, TEST_B AUROC=0.7122; top-vs-bottom predictability quartile accuracy gaps=46.13pp and 44.08pp; 9/9 primary sets positive direction.
**权威来源：** `W1_AUDIT` → `w/FULL/wave1_result.json -> assessment.experiments.E2_PREDICTABILITY`
**状态：** `SUPPORTED_DEVELOPMENT`
**发布用途：** historical motivation

### E003 — NEGATIVE_DEVELOPMENT
**主张：** More complex generic predictive models did not provide a practical upgrade over the strong behavioral baseline in Wave1.
**机器结果：** Wave1 E5 complexity family was DISCONFIRMED versus B2; e.g. pooled regularized logit accuracy delta about -3.56pp; ensemble about -4.11pp.
**权威来源：** `W1_AUDIT` → `w/FULL/wave1_result.json -> assessment.experiments.E5_COMPLEXITY`
**状态：** `NEGATIVE_RESULT`
**发布用途：** failure history / simplicity rationale

### E004 — NEGATIVE_DEVELOPMENT
**主张：** A learned B0/B1/B2 router did not beat simply using B2 on the development windows.
**机器结果：** W2A pooled learned-router vs B2 accuracy delta=-0.1666pp; bootstrap 95% interval approximately [-0.3334,-0.0058]pp; log-score delta=-0.0469.
**权威来源：** `W2A_AUDIT` → `w/FULL/wave2a_result.json -> assessment.E6_ROUTING.E6B_LEARNED_ROUTER`
**状态：** `INCONCLUSIVE_TO_NEGATIVE`
**发布用途：** failure history / no router claim

### E005 — DEVELOPMENT
**主张：** Simple model confidence can support selective prediction, but this result was still on previously observed development windows.
**机器结果：** W2A B2 confidence curve: about 92.3% accuracy at 20% coverage, 84.4% at 40%, 78.0% at 60%, 71.4% at 80%, 65.5% at 100% in TEST_B; similar TEST_A pattern.
**权威来源：** `W2A_AUDIT` → `w/FULL/wave2a_result.json -> assessment.E7_SELECTIVE`
**状态：** `SUPPORTED_DEVELOPMENT`
**发布用途：** historical precursor to P1

### E006 — PRACTICAL_MODEL_SELECTION
**主张：** B2 contains statistically real incremental information over B1, but the average gain is below the predeclared practical complexity threshold; B1 remains the simple default.
**机器结果：** 26,659 nonzero-history events: B1=64.4210%, B2=65.6814%, delta=+1.2604pp. Household-cluster 95% interval about +0.8568 to +1.6575pp; week-cluster about +0.7541 to +1.7492pp. Verdict KEEP_B1_SIMPLE_DEFAULT.
**权威来源：** `CONFIDENCE_AUDIT` → `w/FULL/study_result.json -> practical_decision`
**状态：** `SUPPORTED_REAL_BUT_NOT_PRACTICAL_UPGRADE`
**发布用途：** core simplicity rationale

### E007 — DEVELOPMENT
**主张：** The simple P1 household-stability score captures most of the available predictability-ranking value without a learned gate.
**机器结果：** 9-product development: P1 top20-bottom20 future accuracy gap=40.91pp; accuracy at 60% coverage=71.36% vs 62.30% at 100%; 5/5 forward blocks positive and monotone. P4 logistic improves further but by only ~2.23pp at 60% coverage.
**权威来源：** `FRONTIER_AUDIT` → `w/FULL/summary.json -> gate_summary`
**状态：** `SUPPORTED_DEVELOPMENT`
**发布用途：** formula selection rationale

### E008 — GENERALIZATION_BATCH_1
**主张：** A frozen global P1 gate generalized to a first batch of new, non-development product groups selected without future outcomes.
**机器结果：** 100 selected, 99 evaluable; 52,854 W3-W6 events. GLOBAL_P1_B1: 39.16% coverage / 76.18% accuracy (60 target), 21.49% / 83.55% (70), 11.50% / 88.14% (80).
**权威来源：** `GEN1_AUDIT` → `w/FULL/summary.json -> policy_summary`
**状态：** `EXPLORATORY_SUPPORT_WITH_BREADTH`
**发布用途：** independent first cross-product replication

### E009 — PROVENANCE
**主张：** First-batch product groups were generated from a pre-outcome candidate universe rather than selected on W3-W6 performance.
**机器结果：** Upstream recon found 507 eligible pre-week-22 candidate groups. N001-N100 were selected/materialized using week<=22 metadata/support and fixed ordering; 600 candidate SKUs were unique, with zero overlap to copied legacy sets. W3-W6 outcomes were evaluation-only.
**权威来源：** `GEN1_LINEAGE` → `recon/MRSP_UPSTREAM_SOURCE_RECON_20260921.md + lineage_tools/materialize_gen1_candidates.py + N001_N100 lineage manifest`
**状态：** `PROVENANCE_CONFIRMED`
**发布用途：** core anti-leak provenance

### E010 — CONFIRMATORY_PRIMARY
**主张：** The frozen P1 gate replicated in a second untouched representative product batch with almost the same coverage-accuracy frontier.
**机器结果：** 100 selected, 99 evaluable; 40,474 events. Frozen GLOBAL_P1_B1: 41.08% coverage / 77.17% accuracy (60 target); 22.00% / 84.78% (70); 11.01% / 90.06% (80). No P1 recalibration; B2 and learned gates forbidden.
**权威来源：** `CONFIRM_AUDIT` → `w/FULL/summary.json -> cohort_summary + confirmation_scorecard + spec_assertions`
**状态：** `CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT`
**发布用途：** PRIMARY PUBLIC RESULT

### E011 — CONFIRMATORY_BREADTH
**主张：** The P1 selective-prediction effect also transferred across a deliberately non-Grocery-heavy department challenge cohort.
**机器结果：** 100 selected, 99 evaluable; 36,027 events. At frozen 60-target cutoff: B1-all=61.18%, selective P1=79.33% at 40.22% coverage (+18.15pp). 7 departments had >=5 products; 6/7 passed the predeclared >=10pp gain rule. Produce improved +8.62pp but missed the 10pp rule.
**权威来源：** `CONFIRM_AUDIT` → `w/FULL/summary.json -> department_summary + confirmation_scorecard`
**状态：** `SUPPORTED_CROSS_DEPARTMENT_WITHIN_PANEL`
**发布用途：** PRIMARY BREADTH RESULT

### E012 — CONFIRMATORY_SECONDARY
**主张：** A simple action policy can trade some selective accuracy for more coverage by using B0 when market-level prediction is already adequate and B1 when personalization adds value.
**机器结果：** Second representative batch GLOBAL_SIMPLE_ACTION: 56.60% coverage / 70.87% accuracy (60 target), 29.04% / 80.76% (70), 14.95% / 85.11% (80).
**权威来源：** `CONFIRM_AUDIT` → `w/FULL/summary.json -> cohort_summary; confirmation_scorecard.simple_action_checks`
**状态：** `SUPPORTED_SECONDARY`
**发布用途：** secondary productization result

## 证据边界

- 目前最高证据等级是 **within-panel cross-product confirmation（面板内跨商品确认）**，不是另一零售商、另一消费者面板或另一国家的外部验证。
- 当前任务是**条件式六选一商品选择**：已知家庭在某个固定六候选商品组发生购买时，预测六个 SKU 中哪一个会被选择。不是购买发生预测，也不是下一购物篮预测。
- Coverage（覆盖率）是**事件覆盖率**，不是独立客户占比。一个家庭可在不同商品或不同时间产生多个事件。
- Confirmatory 第二批明确冻结 P1 公式与 cutoff；不得把第二批结果描述为重新调参后的最佳结果。


## E013 — Frozen task definition authority

The public task is **conditional six-alternative SKU choice** within a frozen product group. An evaluable event already contains a purchase in that six-SKU set; the target is which SKU was chosen. Purchase incidence and next-basket prediction are outside this release. Authority: `audit/FORMULA_AUTHORITY.md`, `src/data.py`, `src/models.py`, and `src/predictability.py`.
