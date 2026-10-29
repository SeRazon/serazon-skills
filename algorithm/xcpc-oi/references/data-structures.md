# 数据结构

## 并查集（DSU）

适用：连通性、合并集合、Kruskal、带权关系。

```cpp
struct DSU {
    vector<int> f, sz;
    DSU(int n) : f(n + 1), sz(n + 1, 1) { iota(f.begin(), f.end(), 0); }
    int find(int x) { return f[x] == x ? x : f[x] = find(f[x]); }
    bool merge(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (sz[a] < sz[b]) swap(a, b);
        f[b] = a; sz[a] += sz[b]; return true;
    }
};
```

- 复杂度：路径压缩 + 按大小合并，均摊 O(α(n))。
- 可撤销并查集：不能路径压缩，按秩合并 + 栈记录，O(log n)。
- 带权并查集：维护到根的偏移，注意合并时偏移的方向。

## 树状数组（Fenwick）

```cpp
struct BIT {
    int n; vector<long long> t;
    BIT(int n) : n(n), t(n + 1, 0) {}
    void add(int i, long long v) { for (; i <= n; i += i & -i) t[i] += v; }
    long long sum(int i) { long long s = 0; for (; i > 0; i -= i & -i) s += t[i]; return s; }
    long long range(int l, int r) { return sum(r) - sum(l - 1); }
};
```

| 需求 | 做法 |
|---|---|
| 单点加、区间和 | 一个 BIT |
| 区间加、单点查 | 差分 BIT |
| 区间加、区间和 | 两个 BIT（维护 d 与 i·d） |
| 前缀最大值 | 树状数组改 `max`，只能前缀查询 |

## 线段树

```cpp
struct Seg {
    int n; vector<long long> sum, tag;
    Seg(int n) : n(n), sum(4 * n), tag(4 * n) {}
    void push(int p, int l, int r) {
        if (!tag[p]) return;
        int m = (l + r) >> 1;
        sum[p << 1] += tag[p] * (m - l + 1); tag[p << 1] += tag[p];
        sum[p << 1 | 1] += tag[p] * (r - m); tag[p << 1 | 1] += tag[p];
        tag[p] = 0;
    }
    void add(int p, int l, int r, int ql, int qr, long long v) {
        if (ql <= l && r <= qr) { sum[p] += v * (r - l + 1); tag[p] += v; return; }
        push(p, l, r); int m = (l + r) >> 1;
        if (ql <= m) add(p << 1, l, m, ql, qr, v);
        if (qr > m) add(p << 1 | 1, m + 1, r, ql, qr, v);
        sum[p] = sum[p << 1] + sum[p << 1 | 1];
    }
    long long query(int p, int l, int r, int ql, int qr) {
        if (ql <= l && r <= qr) return sum[p];
        push(p, l, r); int m = (l + r) >> 1; long long s = 0;
        if (ql <= m) s += query(p << 1, l, m, ql, qr);
        if (qr > m) s += query(p << 1 | 1, m + 1, r, ql, qr);
        return s;
    }
};
```

变体：动态开点（值域大）、线段树合并（树上启发式）、可持久化（主席树，查区间第 k 小）、李超树（一次函数最值）、线段树分治（带删除的插入）。

## ST 表（静态 RMQ）

O(n log n) 预处理、O(1) 查询，不支持修改：

```cpp
int lg[N]; int st[20][N];
void build(int n) { lg[1] = 0; for (int i = 2; i <= n; ++i) lg[i] = lg[i / 2] + 1;
  for (int j = 1; (1 << j) <= n; ++j) for (int i = 1; i + (1 << j) - 1 <= n; ++i)
    st[j][i] = min(st[j-1][i], st[j-1][i + (1 << (j-1))]); }
int qry(int l, int r) { int k = lg[r - l + 1]; return min(st[k][l], st[k][r - (1 << k) + 1]); }
```

## 堆与可删堆

- 需要删除任意元素：惰性删除（两个堆，一个存删除标记）或 `multiset`。
- 对顶堆维护中位数：大根堆存较小半，小根堆存较大半，保持大小差 ≤ 1。

## 分块与莫队

- 分块：块长 √n，区间操作 O(√n)，适合"线段树不好维护"的暴力可合并操作。
- 普通莫队：离线、无修改、区间查询可 O(1) 增删；复杂度 O(n√n)。
- 带修莫队：块长 n^(2/3)，多一维时间。
- 回滚莫队：只能加不能删时使用。

## 平衡树选型

| 需求 | 建议 |
|---|---|
| 只要有序集合 + 前驱后继 | `std::set` / `multiset` |
| 排名、第 k 小、插入删除 | pb_ds `tree` 或 Treap |
| 区间翻转、分裂合并 | FHQ Treap / Splay |
| 可持久化 | 可持久化 Treap / 主席树 |

比赛优先用 `pb_ds`，实现量最小；需要区间操作再上 FHQ Treap。

## 选择速查

| 操作特征 | 首选 |
|---|---|
| 只有合并、查询连通 | DSU |
| 前缀信息、单点更新 | BIT |
| 区间更新 + 区间查询 | 线段树 |
| 静态区间最值 | ST 表 |
| 离线区间、可增删 | 莫队 |
| 值域大、动态第 k | 主席树 / 平衡树 |
