# 基础与复杂度

## 复杂度速判

- 时间：主循环次数 × 单次操作代价；注意 `std::map` / `set` 每次 O(log n)，`unordered_map` 期望 O(1) 但可被卡。
- 空间：`int` 4B、`long long` 8B；1e7 个 `int` ≈ 40MB，接近常见 256MB 限制的三分之一。
- 递归：栈深超过 1e5 有爆栈风险，改迭代或手动开栈。

## 二分

三种形态，先写对再优化：

```cpp
// 1) 找第一个 >= x 的位置
int l = 0, r = n;              // [l, r)
while (l < r) { int m = (l + r) >> 1; if (a[m] >= x) r = m; else l = m + 1; }
// 2) 答案二分：check(mid) 单调
while (l < r) { int m = (l + r + 1) >> 1; if (check(m)) l = m; else r = m - 1; }
// 3) 浮点：固定迭代 100 次，别用 eps 判等
for (int it = 0; it < 100; ++it) { double m = (l + r) / 2; (check(m) ? l : r) = m; }
```

坑：`(l + r) >> 1` 在负数上不是向下取整；`l + r` 可能溢出，用 `l + (r - l) / 2`。

## 双指针

适用条件：**单调性**（窗口扩大/缩小时判定单调）。典型：最短覆盖子串、两数之和（有序）、去重、滑动窗口最值（配单调队列）。

## 前缀和与差分

| 需求 | 做法 |
|---|---|
| 区间和查询 | 一维前缀和 O(n) 预处理 + O(1) 查询 |
| 区间加、单点查 | 差分数组 |
| 区间加、区间和 | 两个树状数组或线段树 |
| 二维子矩阵和 | 二维前缀和，容斥四条边 |

二维前缀：`s[i][j] = a[i][j] + s[i-1][j] + s[i][j-1] - s[i-1][j-1]`。

## 离散化

值域大但只关心相对顺序时使用：

```cpp
vector<int> v = a; sort(v.begin(), v.end()); v.erase(unique(v.begin(), v.end()), v.end());
for (auto &x : a) x = lower_bound(v.begin(), v.end(), x) - v.begin() + 1;
```

## 贪心

两个可靠论证工具：

1. **交换论证**：假设最优解与贪心选择不同，交换后不更差。
2. **归纳/拟阵**：证明每步局部最优可扩展为全局最优。

反例优先：先试 `n = 2`、`n = 3` 能否推翻。排序关键字要写成**严格弱序**（相等返回 false），否则 `sort` 可能越界。

## 构造

- 先看小规模手玩，找周期/对称/奇偶性。
- 常见套路：配对、镜像、按奇偶分组、从后往前填。
- 校验：写个 checker 暴力验证构造合法性。

## 位运算

| 操作 | 写法 |
|---|---|
| 取最低位 1 | `x & -x` |
| 去掉最低位 1 | `x & (x - 1)` |
| 子集枚举 | `for (int s = m; ; s = (s - 1) & m) { ...; if (!s) break; }` |
| 二进制位数 | `__builtin_popcount` / `__builtin_ctz` / `__builtin_clz` |

`1 << 31` 是 UB（有符号溢出），用 `1LL << 31`。

## STL 常见坑

- `priority_queue` 默认**大根堆**；小根用 `greater<int>`。
- `vector` 频繁 `push_back` 先 `reserve`。
- `map::operator[]` 会插入默认值；查询用 `find`。
- `string::substr` 每次拷贝，循环里用 `string_view`。
- `sort` 比较器里不要写 `<=`。
- 迭代器失效：`vector` 扩容后旧迭代器全部失效。
