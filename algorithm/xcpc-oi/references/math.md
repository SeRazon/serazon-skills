# 数学

## 模运算基础

```cpp
long long qpow(long long a, long long b, long long p) {
    long long r = 1 % p; a %= p;
    for (; b; b >>= 1, a = a * a % p) if (b & 1) r = r * a % p;
    return r;
}
```

- 乘法溢出：模数 > 1e9 时用 `__int128` 或龟速乘。
- 减法取模：`(a - b % p + p) % p`。

## 逆元

| 条件 | 方法 |
|---|---|
| p 为质数，a 不是 p 的倍数 | 费马小定理 `a^(p-2)` |
| gcd(a, p) = 1 | 扩展欧几里得 |
| 求 1..n 全部逆元 | 线性递推 `inv[i] = -(p/i) * inv[p%i] % p` |

## 筛法

```cpp
vector<int> primes; vector<bool> comp(n + 1);
for (int i = 2; i <= n; ++i) {
    if (!comp[i]) primes.push_back(i);
    for (int p : primes) { if (1LL * i * p > n) break; comp[i * p] = true; if (i % p == 0) break; }
}
```

线性筛可顺带求欧拉函数、莫比乌斯函数、约数个数。

## 积性函数与反演

- 常见积性函数：`φ(n)`、`μ(n)`、`d(n)`、`σ(n)`。
- 莫比乌斯反演常用形式：`Σ_{d|n} μ(d) = [n = 1]`，把 `gcd` 计数转成枚举约数。
- 套路：先写暴力 `ΣΣ [gcd(i,j)=1]`，再用 `Σ_{d|gcd} μ(d)` 换序，最后数论分块 O(√n)。

## 同余方程

- 一元线性同余 `ax ≡ b (mod m)`：先 `g = gcd(a, m)`，`g ∤ b` 无解；否则化为 `a/g · x ≡ b/g (mod m/g)`，用扩欧求逆。
- CRT：模数两两互质时直接合并；不互质用 EXCRT（合并时判 `g | (b2 - b1)`）。

## 组合数学

```cpp
// 预处理阶乘与逆元，O(n) 查询 C(n, m)
fact[0] = 1; for (int i = 1; i <= N; ++i) fact[i] = fact[i-1] * i % MOD;
invfact[N] = qpow(fact[N], MOD - 2, MOD);
for (int i = N; i; --i) invfact[i-1] = invfact[i] * i % MOD;
auto C = [&](int n, int m) { return m < 0 || m > n ? 0LL : fact[n] * invfact[m] % MOD * invfact[n-m] % MOD; };
```

- n 很大、模数小：Lucas 定理。
- 卡特兰数：`C(2n, n) / (n + 1)`，场景：合法括号、出栈序列、二叉树计数。
- 斯特林数：第二类 `S(n, k) = S(n-1, k-1) + k·S(n-1, k)`，场景：集合划分。

## 容斥

`|A₁ ∪ … ∪ Aₙ| = Σ|Aᵢ| − Σ|Aᵢ∩Aⱼ| + …`；n ≤ 20 时二进制枚举子集，按 popcount 奇偶加减。

## 矩阵与线性代数

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
```

- 矩阵快速幂求线性递推第 n 项（斐波那契、走 k 步方案数）。
- 高斯消元：实数用 `fabs` 选主元 + eps；异或方程组用 bitset 加速。
- 行列式：消元时记录交换次数符号。

## 博弈论

- Nim：异或和非 0 先手必胜。
- SG 定理：`SG(u) = mex{SG(v)}`，多堆异或为 0 必败。
- 阶梯博弈、反 Nim 需单独记结论。

## 概率与期望

- 期望线性性优先；有环时列方程（高斯消元），无环按拓扑倒推。
- 几何分布期望 `1/p`；全期望公式 `E[X] = Σ P(Y=y) E[X|Y=y]`。

## 常见坑

1. 模数为合数时不能用费马小定理求逆。
2. 负数取模、`int` 乘 `int` 溢出。
3. 筛法上界写小（要 `n + 1`）。
4. 组合数预处理忘记 `invfact[0] = 1`。
5. 浮点比较用 `eps`，几何题优先整数运算。
