# 字符串与计算几何

## 字符串哈希

```cpp
// 双模更稳；单模有被构造碰撞的风险
const long long B = 131, M1 = 1e9 + 7, M2 = 1e9 + 9;
vector<long long> h1(n + 1), h2(n + 1), p1(n + 1, 1), p2(n + 1, 1);
for (int i = 1; i <= n; ++i) {
    h1[i] = (h1[i-1] * B + s[i]) % M1; p1[i] = p1[i-1] * B % M1;
    h2[i] = (h2[i-1] * B + s[i]) % M2; p2[i] = p2[i-1] * B % M2;
}
auto get = [&](int l, int r) {
    return pair{(h1[r] - h1[l-1] * p1[r-l+1] % M1 + M1) % M1,
                (h2[r] - h2[l-1] * p2[r-l+1] % M2 + M2) % M2};
};
```

- 自然溢出（`unsigned long long`）快，但可被卡；重要比赛用双模。
- 回文判定：正串与反串哈希比较。

## KMP

`nxt[i]` 表示 `s[1..i]` 的最长真前缀等于后缀的长度。

```cpp
vector<int> getNext(const string &s) {
    int n = s.size(); vector<int> nxt(n);
    for (int i = 1, j = 0; i < n; ++i) {
        while (j && s[i] != s[j]) j = nxt[j-1];
        if (s[i] == s[j]) ++j;
        nxt[i] = j;
    }
    return nxt;
}
```

- 匹配：文本串上跑同样的失配逻辑，`j == m` 时命中，回退 `j = nxt[m-1]`。
- 最小循环节：`n - nxt[n-1]`，若 `n % 该值 == 0` 则为整周期。

## Z 函数

`z[i]` = `s` 与 `s[i..]` 的最长公共前缀长度。线性时间，适合求每个后缀与原串的匹配长度。

## Manacher

求最长回文子串 O(n)：插入分隔符 `#` 统一奇偶，维护当前最右回文边界 `[l, r]`，`p[i] = min(r - i + 1, p[2*l - i])` 后再暴力扩展。

## Trie 与 01-Trie

- 普通 Trie：前缀查询、字典序、异或最大值（01-Trie）。
- 01-Trie 求最大异或对：按位从高到低走相反分支。
- 可持久化 01-Trie：区间异或最大值。

## AC 自动机

1. 所有模式串建 Trie；
2. BFS 求 `fail` 指针（失配后跳到最长后缀）；
3. 文本串上沿 `fail` 走，统计命中。

- 多个模式串同时匹配、禁词过滤、DP 套 AC 自动机（长度 n 的串不含禁词）。
- 优化：`fail` 树 + 拓扑排序，避免暴力跳 `fail`。

## 后缀数组（SA）

倍增 + 基数排序 O(n log n)，`sa[i]` 为排名第 i 的后缀起点，`height[i] = LCP(sa[i-1], sa[i])`。

- 本质不同子串数：`n(n+1)/2 - Σ height`。
- 两个后缀的 LCP = `height` 区间最小值（配 ST 表）。
- 后缀自动机（SAM）：状态数 ≤ 2n，可求本质不同子串、endpos 大小、最长公共子串。

## 计算几何

### 基础运算

```cpp
struct P { long long x, y; };
P operator-(P a, P b) { return {a.x - b.x, a.y - b.y}; }
long long cross(P a, P b) { return a.x * b.y - a.y * b.x; }   // >0 逆时针
long long dot(P a, P b)   { return a.x * b.x + a.y * b.y; }
```

- **整数优先**：能用 `long long` 就别用 `double`，避免精度问题。
- 必须用浮点时，比较写 `fabs(x) < eps`（eps 取 1e-9），不要用 `==`。

### 判定

| 问题 | 方法 |
|---|---|
| 点在线段上 | 叉积为 0 且投影在段内 |
| 两线段相交 | 跨立实验（两次叉积异号）+ 共线特判 |
| 点在多边形内 | 射线法（奇偶）或转角法 |
| 凸多边形面积 | 叉积和的一半（注意方向） |

### 凸包（Andrew）

按 x 排序，分别求上下凸壳，去掉共线点则用 `cross <= 0` 弹出。复杂度 O(n log n)。

### 旋转卡壳

在凸包上求直径、最小矩形覆盖、点集最大距离，O(n)。

### 扫描线

矩形面积并：按 x 排序事件，线段树维护 y 方向覆盖长度与覆盖次数。

## 常见坑

1. 哈希基数太小或模数被卡。
2. KMP 的 `nxt` 用 0-index 与 1-index 混写。
3. 几何题叉积溢出（坐标 1e9 时用 `__int128`）。
4. 凸包共线点处理不一致导致 WA。
5. 浮点 `eps` 过大吞掉合法答案，过小则死循环。
