# 算法条目模板

## 条目卡片

```markdown
### <算法名>

**适用条件**
- 题型：TODO
- 约束：TODO（如无负权边、静态区间、单点更新）

**复杂度**
- 时间：O(TODO)
- 空间：O(TODO)
- 常数提示：TODO

**边界与坑**
- 空输入 / 单点：TODO
- 极值：TODO（溢出、精度、栈深）
- 平台差异：TODO

**实现要点**
1. TODO
2. TODO

**代码**
```cpp
// TODO：最少可运行实现
```
```

## 对拍三件套

```bash
# gen.cpp：生成随机数据（含边界）
# brute.cpp：暴力
# fast.cpp：正解
for i in $(seq 1 1000); do
  ./gen > in.txt
  ./brute < in.txt > a.txt
  ./fast  < in.txt > b.txt
  diff -q a.txt b.txt > /dev/null || { echo "WA on $i"; break; }
done
```

## 自检

- [ ] 适用条件写清楚了吗（不成立时会错在哪）
- [ ] 复杂度与数据范围匹配
- [ ] 代码能编译，无未定义行为
- [ ] 标出了需要按题意改动的位置
- [ ] 至少跑过一次对拍
