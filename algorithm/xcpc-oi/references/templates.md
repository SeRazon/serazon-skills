# C++17 模板

> 直接复制可用，但**必须按题意改**：多测清空、取模、`long long`、数组大小。

## 快读

```cpp
static char buf[1 << 20], *p1 = buf, *p2 = buf;
inline char gc() { return p1 == p2 && (p2 = (p1 = buf) + fread(buf, 1, 1 << 20, stdin), p1 == p2) ? EOF : *p1++; }
template <class T> inline void read(T &x) {
    x = 0; int f = 1; char c = gc();
    while (c < '0' || c > '9') { if (c == '-') f = -1; c = gc(); }
    while (c >= '0' && c <= '9') { x = x * 10 + (c ^ 48); c = gc(); }
    x *= f;
}
```

## 并查集

```cpp
struct DSU {
    vector<int> f, sz;
    DSU(int n) : f(n + 1), sz(n + 1, 1) { iota(f.begin(), f.end(), 0); }
    int find(int x) { while (x != f[x]) x = f[x] = f[f[x]]; return x; }
    bool merge(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (sz[a] < sz[b]) swap(a, b);
        f[b] = a; sz[a] += sz[b];
        return true;
    }
};
```

## 树状数组

```cpp
struct BIT {
    int n; vector<long long> t;
    BIT(int n) : n(n), t(n + 1) {}
    void add(int i, long long v) { for (; i <= n; i += i & -i) t[i] += v; }
    long long sum(int i) { long long s = 0; for (; i > 0; i -= i & -i) s += t[i]; return s; }
    long long query(int l, int r) { return sum(r) - sum(l - 1); }
};
```

## 线段树（区间加、区间和）

```cpp
struct SegTree {
    int n; vector<long long> sum, tag;
    SegTree(int n) : n(n), sum(4 * n), tag(4 * n) {}
    void apply(int p, int l, int r, long long v) { sum[p] += v * (r - l + 1); tag[p] += v; }
    void push(int p, int l, int r) {
        if (!tag[p] || l == r) return;
        int m = (l + r) >> 1;
        apply(p << 1, l, m, tag[p]); apply(p << 1 | 1, m + 1, r, tag[p]); tag[p] = 0;
    }
    void add(int p, int l, int r, int ql, int qr, long long v) {
        if (ql <= l && r <= qr) { apply(p, l, r, v); return; }
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

## Dijkstra

```cpp
vector<long long> dijkstra(int s, int n, const vector<vector<pair<int,int>>> &g) {
    const long long INF = (long long)4e18;
    vector<long long> d(n + 1, INF); vector<char> vis(n + 1);
    priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>> pq;
    d[s] = 0; pq.push({0, s});
    while (!pq.empty()) {
        auto [du, u] = pq.top(); pq.pop();
        if (vis[u]) continue; vis[u] = 1;
        for (auto [v, w] : g[u]) if (du + w < d[v]) d[v] = du + w, pq.push({d[v], v});
    }
    return d;
}
```

## Kruskal

```cpp
struct Edge { int u, v; long long w; };
long long kruskal(int n, vector<Edge> &e) {
    sort(e.begin(), e.end(), [](auto &a, auto &b) { return a.w < b.w; });
    DSU dsu(n); long long ans = 0; int cnt = 0;
    for (auto &x : e) if (dsu.merge(x.u, x.v)) { ans += x.w; if (++cnt == n - 1) break; }
    return cnt == n - 1 ? ans : -1;   // -1 表示不连通
}
```

## 倍增 LCA

```cpp
int LOG; vector<vector<int>> up; vector<int> dep;
void dfs(int u, int fa, const vector<vector<int>> &g) {
    up[0][u] = fa; dep[u] = dep[fa] + 1;
    for (int k = 1; k < LOG; ++k) up[k][u] = up[k-1][up[k-1][u]];
    for (int v : g[u]) if (v != fa) dfs(v, u, g);
}
int lca(int u, int v) {
    if (dep[u] < dep[v]) swap(u, v);
    int d = dep[u] - dep[v];
    for (int k = 0; k < LOG; ++k) if (d >> k & 1) u = up[k][u];
    if (u == v) return u;
    for (int k = LOG - 1; k >= 0; --k) if (up[k][u] != up[k][v]) u = up[k][u], v = up[k][v];
    return up[0][u];
}
```

## 矩阵快速幂

```cpp
struct Mat {
    int n; vector<vector<long long>> a;
    Mat(int n) : n(n), a(n, vector<long long>(n)) {}
    Mat operator*(const Mat &o) const {
        Mat r(n);
        for (int i = 0; i < n; ++i) for (int k = 0; k < n; ++k) if (a[i][k])
            for (int j = 0; j < n; ++j) r.a[i][j] = (r.a[i][j] + a[i][k] * o.a[k][j]) % MOD;
        return r;
    }
};
Mat mpow(Mat b, long long e) {
    Mat r(b.n); for (int i = 0; i < b.n; ++i) r.a[i][i] = 1;
    for (; e; e >>= 1, b = b * b) if (e & 1) r = r * b;
    return r;
}
```

## 组合数预处理

```cpp
vector<long long> fact(N + 1), invfact(N + 1);
fact[0] = 1; for (int i = 1; i <= N; ++i) fact[i] = fact[i-1] * i % MOD;
invfact[N] = modpow(fact[N], MOD - 2);
for (int i = N; i; --i) invfact[i-1] = invfact[i] * i % MOD;
long long C(int n, int m) { return (m < 0 || m > n) ? 0 : fact[n] * invfact[m] % MOD * invfact[n-m] % MOD; }
```

## 字符串哈希（双模）

```cpp
const long long B1 = 131, M1 = 1000000007, B2 = 13331, M2 = 1000000009;
// 预处理 p1/p2 与 h1/h2，区间哈希见 references/strings-geometry.md
```

## 对拍脚本

```bash
#!/usr/bin/env bash
# 用法：./check.sh gen brute fast 1000
GEN=$1; BRUTE=$2; FAST=$3; N=${4:-1000}
for ((i=1;i<=N;i++)); do
  ./"$GEN" > in.txt
  ./"$BRUTE" < in.txt > a.txt
  ./"$FAST"  < in.txt > b.txt
  diff -q a.txt b.txt > /dev/null || { echo "WA on case $i"; break; }
done
```
