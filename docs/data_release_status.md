# Data Release Status（资料公开状态）

## 当前本机来源谱系

上游 Recon 记录：

- `C:\MR\data\CJ_R\transactions.rds`：1,469,307 rows，weeks 1–53，2,469 households，68,509 products；
- `promotions.rds`：20,940,529 rows；
- `completejourney_1.1.1.tar.gz`：product metadata source；
- canonical store：`C:\MR\data\CJ9`。

## 外部授权线索

- `completejourney` R package 的 `DESCRIPTION` 声明 `License: CC0`。
- dunnhumby 官方 Source Files / 网站条款将网站材料描述为研究／个人／非商业用途，并保留其他权利。

## R1 决策

**原始／逐事件消费数据暂不打包进公开 GitHub Release。**

原因：目前还没有把本机 `transactions.rds` 的实际取得路径与适用授权条款逐文件闭环到“可公开再分发”的程度。不同镜像／套件的授权表述并不完全一致。

## 不受影响的公开内容

即使暂不再分发原始资料，也可以公开：

- 全部研究程式；
- B0/B1/P1 公式；
- config / cutoff / time windows；
- schema；
- source hashes；
- candidate / selection registry（若不含受限逐行交易资料）；
- aggregate result tables；
- synthetic miniature dataset（合成小资料）；
- expected results / tests；
- 使用者自行取得原始资料后的完整重现步骤。

## 第二轮前待办

在真正 public release 前做一次专门 License Audit（授权审计）：确认本机 RDS 是否直接来自 CC0 `completejourney` package，还是来自 dunnhumby/Kaggle 另一授权路径。除非闭环，否则沿用“不附原始资料”的安全发布策略。
