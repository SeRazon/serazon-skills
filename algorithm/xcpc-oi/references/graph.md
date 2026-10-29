# 图论

## 存图

```cpp
vector<vector<pair<int,int>>> g(n + 1);   // (to, w)，1-index
// 链式前向星：点多边多、需要遍历反向边时用
```

坑：重边取最小、自环单独判、`1-index` 与 `0-index` 不要混。

## 最短路

| 算法 | 适用 | 复杂度 | 备注 |
|---|---|---|---|
| Dijkstra（堆优化） | 非负权 | O((n+m) log n) | 首选 |
| Bellman-Ford | 有负权、判负环 | O(nm) | 跑 n 轮仍可松弛 → 负环 |
| SPFA | 负权 | 最坏 O(nm) | **可被网格图卡死**，非必要不用 |
| Floyd | 全源、n ≤ 500 | O(n³) | 可求传递闭包、最小环 |

```cpp
vector<long long> dijkstra(int s, int n, vector<vector<pair<int,int>>> &g) {
    const long long INF = 4e18;
    vector<long long> d(n + 1, INF); vector<char> vis(n + 1);
    priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>> pq;
    d[s] = 0; pq.push({0, s});
    while (!pq.empty()) {
        auto [du, u] = pq.top(); pq.pop();
        if (vis[u]) continue; vis[u] = 1;
        for (auto [v, w] : g[u]) if (du + w < d[v]) { d[v] = du + w; pq.push({d[v], v}); }
    }
    return d;
}
```

`INF` 取 `4e18`，别用 `INT_MAX`（相加溢出成负数）。

## 最小生成树

- **Kruskal**：按边权排序 + DSU，O(m log m)；稀疏图首选。
- **Prim**：O(n²)（朴素，稠密图）或 O(m log n)（堆优化）。
- 次小生成树：先求 MST，再枚举非树边替换路径最大边。

## 拓扑排序

BFS 入度法；若输出字典序最小，把队列换成小根堆。若排完不足 n 个点 → 有环。

## 连通性（Tarjan）

```text
dfn[u]：首次访问时间；low[u]：能回到的最早 dfn
SCC：low[u] == dfn[u] 时弹栈，栈中元素构成一个强连通分量
割点：非根节点 low[v] >= dfn[u]；根节点需 ≥ 2 个这样的儿子
桥：  low[v] > dfn[u]
```

- SCC 缩点后得到 DAG，可做 DAG 上 DP（最长路、方案数）。
- 无向图边双连通分量：删桥后剩下的连通块。

## 2-SAT

每个变量拆成 `x` 与 `¬x` 两个点，条件 `a ∨ b` 建边 `¬a → b`、`¬b → a`，跑 SCC：同变量两点在同一 SCC → 无解；否则 `x` 取 `scc[x] > scc[¬x]`（Tarjan 编号顺序）或按拓扑序取反。

## 二分图

- 判定：BFS/DFS 染色，冲突即非二分图。
- 最大匹配：匈牙利 O(VE)（n ≤ 500 可用）；Hopcroft-Karp O(E√V)。
- 带权最大匹配：KM O(n³)；最小点覆盖 = 最大匹配；最大独立集 = n − 最大匹配。
- 建模信号：任务分配、棋盘染色、冲突分组。

## LCA 与树上问题

```cpp
// 倍增：up[k][u] 表示 u 向上 2^k 步
int lca(int u, int v) {
    if (dep[u] < dep[v]) swap(u, v);
    for (int k = 19; k >= 0; --k) if (dep[u] - (1 << k) >= dep[v]) u = up[k][u];
    if (u == v) return u;
    for (int k = 19; k >= 0; --k) if (up[k][u] != up[k][v]) { u = up[k][u]; v = up[k][v]; }
    return up[0][u];
}
```

- 树上差分：点差分 `d[u]++, d[v]++, d[lca]--, d[fa[lca]]--`；边差分把 `d[lca]` 减两次。
- 树剖：路径查询/修改 O(log²n)；也可求 LCA。
- 换根、子树统计：先 DFS 序转区间，再上数据结构。

## 网络流

- **Dinic**：O(V²E) 上界，实际远快；BFS 分层 + DFS 多路增广 + 当前弧优化。
- 最大流 = 最小割；二分图最大匹配 = 单位容量最大流。
- 常见建模：拆点（点容量）、上下界（先满足下界再补流）、费用流（SPFA/Dijkstra 找增广路）。
- 坑：边数开两倍、`long long` 流量、当前弧每次 BFS 重置。

## 常见坑

1. 多测不清空邻接表 / 访问标记。
2. Dijkstra 用了负权边（结果错但不报错）。
3. 递归 DFS 深度 1e5 以上爆栈。
4. 无向图建边忘记反向边容量。
5. 图的点数按 `n` 开，但编号到 `n + m`（网络流拆点）。
