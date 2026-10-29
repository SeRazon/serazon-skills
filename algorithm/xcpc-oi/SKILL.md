---
name: xcpc-oi
display_name: XCPC / OI 算法竞赛
description: 算法竞赛（ICPC / CCPC / XCPC / OI）的算法选型、复杂度判断、模板实现与赛场流程：按主题给出适用条件、复杂度、常见坑，附 C++17 模板与对拍脚本。刷题、备赛、写题解、卡题时使用。
author: 星鸿SeRazon
license: MIT
---

# XCPC / OI 算法竞赛

面向竞赛的**决策型**知识库：先判断该用什么、复杂度够不够，再动手写；写完必须能自证边界。

## 何时使用

- 看到题不知道往哪个方向想（图论？DP？数学？）
- 不确定数据范围对应的复杂度上限
- 需要一份可靠的 C++17 模板（并查集、线段树、最短路、LCA…）
- 赛后复盘：WA / TLE / RE 定位
- 写题解、出题、造数据与对拍

## 三条铁律

1. **先算复杂度，再写代码**：数据范围 1e5 就别想 O(n²)；1e9 只能 O(log n) / O(1)。
2. **先想边界，再交题**：空输入、单点、全相同、极值、多测清空、取模负数。
3. **先对拍，再提交**：随机小数据 + 暴力，跑 1e3 组；AC 不等于正确。

## 数据范围 → 复杂度（经验表）

| n | 可用复杂度 | 典型算法 |
|---|---|---|
| ≤ 10 | O(n!) / O(n·2ⁿ) | 全排列、状压枚举 |
| ≤ 20 | O(2ⁿ·n) | 状压 DP、折半搜索 |
| ≤ 100 | O(n³) | Floyd、区间 DP、高斯消元 |
| ≤ 500 | O(n³) 常数小 / O(n² log n) | 矩阵乘、KM |
| ≤ 5e3 | O(n²) | 朴素 DP、完全图 |
| ≤ 1e5 | O(n log n) | 排序、树状数组、线段树、Dijkstra |
| ≤ 1e6 | O(n) / O(n log n) 常数小 | 线性筛、单调队列、KMP |
| ≤ 1e7 | O(n) 且常数极小 | 快读 + 手写循环 |
| ≤ 1e9 | O(log n) / O(1) | 快速幂、数论、矩阵 |

## 主题索引

| 主题 | 文件 | 关键内容 |
|---|---|---|
| 基础与复杂度 | [references/basics.md](references/basics.md) | 二分、双指针、前缀差分、离散化、贪心、位运算、STL 坑 |
| 数据结构 | [references/data-structures.md](references/data-structures.md) | DSU、树状数组、线段树、ST 表、分块、莫队、平衡树选型 |
| 图论 | [references/graph.md](references/graph.md) | 最短路、MST、拓扑、SCC、2-SAT、二分图、LCA、网络流 |
| 动态规划 | [references/dp.md](references/dp.md) | 背包、区间、树形、状压、数位、期望、四类优化 |
| 数学 | [references/math.md](references/math.md) | 逆元、筛法、组合数、容斥、矩阵、高斯消元、博弈 |
| 字符串与几何 | [references/strings-geometry.md](references/strings-geometry.md) | 哈希、KMP、Z、Manacher、AC 自动机、SA；凸包、叉积、精度 |
| 赛场与调试 | [references/contest.md](references/contest.md) | 读题清单、分工、对拍、卡常、WA/TLE/RE 定位 |
| 模板 | [references/templates.md](references/templates.md) | C++17 可直接复制的实现 + 对拍脚本 |

## 解题流程

```text
读题 → 数据范围 → 猜复杂度上界 → 枚举可行算法（按主题索引）
     → 验证正确性（交换论证/归纳/反例）
     → 估实现量 → 写 → 小样例 → 暴力对拍 → 造边界 → 提交
```

## 交付物

题解或方案应包含：**思路来源（为什么想到）→ 正确性论证 → 复杂度 → 边界处理 → 代码**。只给代码不算完成。

## 边界

- 模板是起点不是答案：必须按题意改（多测清空、取模、long long、迭代代替递归）。
- 不保证 AC；不代替系统训练。延伸阅读见下方链接，**仅链接不转载**。
- 平台差异（C++ 标准、栈大小、I/O 速度）以赛场环境为准。

## 延伸阅读（仅链接）

- [OI Wiki](https://oi-wiki.org/)：中文竞赛知识体系，覆盖最全（CC BY-SA 4.0）
- [cp-algorithms](https://cp-algorithms.com/)：英文算法实现与证明（CC BY-SA 4.0）
- [ohmyxcpc](https://github.com/L-1ngg/ohmyxcpc)：现代 C++ 码风模板库
- [XCPC-template](https://github.com/ai-lh/XCPC-template)：Markdown + Pandoc 生成打印版模板

> 上述内容许可与本仓库不同，使用与再分发时请遵守其条款；本技能正文与代码为原创整理。

