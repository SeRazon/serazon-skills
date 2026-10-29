# 证据表模板

## claims.csv

```csv
claim_id,claim_text,type,source_ids,status
C001,待填写的事实性断言,事实,S001,已核验
C002,作者自己的判断,观点,,作者观点
C003,待补充来源的断言,事实,,未查到
```

- `claim_id`：`C` + 至少 3 位数字；正文用 `C001` 这样的编号回指。
- `type`：`事实` / `观点` / `数据`。
- `source_ids`：来源编号，多个用 `;` 分隔（如 `S001;S002`）。
- `status`：`已核验` / `未查到` / `待核实`；`观点` 类可用 `作者观点`。
- `事实` / `数据` 标为 `已核验` 时必须至少有一个来源，且来源本身也是 `已核验`。
- `未查到` / `待核实` 的断言不得写入正文的事实部分。

## sources.json

```json
[
  {
    "id": "S001",
    "title": "论文标题",
    "authors": "Firstname Lastname, ...",
    "year": 2026,
    "venue": "期刊或会议",
    "identifier": "DOI 或数据库链接",
    "verified": "已核验"
  }
]
```

- `id`：`S` + 至少 3 位数字。
- `verified`：`已核验` / `未查到` / `待核实`；标为 `已核验` 时 `identifier` 不应为空。

## 使用说明

1. 先建表再写正文：正文里的每个数字与结论都要能回指 `C` 编号。
2. 一条断言可以对应多条来源，用 `;` 分隔；一条来源可被多条断言引用。
3. 交付前运行审计脚本，不要只靠肉眼反查（`SKILL_DIR` 为 `SKILL.md` 所在目录，命令在项目目录执行）：

   ```bash
   python "<SKILL_DIR>/scripts/audit_claims.py" \
     --claims claims.csv \
     --sources sources.json \
     manuscript.md
   ```

4. 交付时附"待核实清单"，列明 `status` 非"已核验"的条目。

## 审计判定

- 正文 `C###` 不在 `claims.csv`：错误。
- 正文 `S###` 不在 `sources.json`：错误。
- `claims.csv` 的 `source_ids` 指向不存在的来源：错误。
- `未查到` / `待核实` 的断言出现在事实段：错误。
- 已核验断言引用未核验来源：错误。
- 已核验的事实 / 数据断言没有来源：错误。
- 默认允许未核验内容出现在「待核实 / 待核验 / 未核实 / 未核验 / 待办 / 附录 / 参考文献 / 致谢」章节；其他章节视为事实段，可用 `--allow-unverified-in` 追加。
