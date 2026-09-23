# Failure History Draft（失败实验／修复历史草案）

公开版建议保留这些会改变科学可信度的失败，不保留纯日志噪音。

| 阶段 | 问题 | 后果 | 修复／最终状态 |
|---|---|---|---|
| V0.7 | row-order state 缺可靠 timestamp | 强结果不能解释为真实时间状态 | 放弃该机制主张 |
| V0.8 | choice set 混合不同品类；k>0 切 uniform prior | 人为制造选择与 prior artifact | V0.9 改同品类 six-choice + 连续 market prior |
| V0.10 | H3 early group 含 k=0 | baseline-first 判定有机械偏差 | 深审后降级；不作为冻结事实 |
| V0.10 | H4 缺 nested ablation | 不能证明 entropy 有独立 shrinkage 价值 | 降为 promising / pending |
| V0.11 | H2 fixed cohort `>=10` 与 k>=10 的事件定义错一位 | 原 SUPPORTED 不可接受 | R1 改 >=11；只剩2合格 set，DATA_LIMITED |
| V0.11 | H4 pooled context 正效应由 H01 主导且 leave-one-set-out 变号 | 不能称通用第三轴 | INCONCLUSIVE / set-dependent |
| Wave2A | learned router | 没有打败 B2，log score 更差 | 不部署 router |
| Wave2B | switch specialist / cold start / hard-case rescue | 多数没有稳定改善，部分明显伤害 | DISCONFIRMED / INCONCLUSIVE |
| PHCM | 单一短 TUNE 选择商品×历史模型 | 未来窗口不稳定 | 改 walk-forward；最终停止复杂路由 |
| Confidence | 未来准确率区间过宽或覆盖不足 | 不能把“历史稳定”直接当未来准确率可信区间 | 转向可预测性 gate |
| Predictability Frontier | P2/P3 商品项在商品内只是单调变换，无法改变排序 | 看似测商品 effect，实际没识别 | 不采用；后续 Action Map 重构商品与家庭两轴 |
| Predictability Frontier | C01-C03 曾因 control flag 漏写进入 P4 训练 | P4 control-transfer 证据不干净 | 排除后重算 P4 主结果几乎不变；后续包加入 machine assertion |
| Generalization V1 初跑 | 假设 cat 目录已有30–100新商品，实际 eligible=0 | preflight fail-closed | 回溯 upstream builder，从 CJ9 pre22 重建 507 候选 |
| Generalization provenance | 初始 audit 未完整封装 N001-N100 生成谱系 | 泛化证据等级暂缓 | 补 upstream upload / lineage hash manifest 后闭环 |

## 公开叙事原则

失败实验的用途不是“展示研究很辛苦”，而是证明最终简单规则不是从大量候选中只挑漂亮结果：关键复杂路线曾被明确测试、发现边界并被丢弃。
