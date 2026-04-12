# Save as verify_fixes.py and run: python verify_fixes.py
import re

checks = []

with open('tasks.py', encoding='utf-8') as f:
    t = f.read()
checks.append(("tasks.py: clean_transactions present", "clean_transactions" in t))
checks.append(("tasks.py: merge_transactions(df1, df2) gone", "merge_transactions(df1, df2)" not in t))

with open('graders.py', encoding='utf-8') as f:
    g = f.read()
checks.append(("graders.py: fence stripping present", "_re.sub" in g))
checks.append(("graders.py: int row count check", "isinstance(expected, int)" in g))
checks.append(("graders.py: no 0.25 floor", "max(0.25" not in g))
checks.append(("graders.py: no 0.15 floor", "max(0.15" not in g))
checks.append(("graders.py: no reward=0.2 floor", "reward=0.2," not in g))

with open('inference.py', encoding='utf-8') as f:
    i = f.read()
checks.append(("inference.py: router URL", "router.huggingface.co" in i))
checks.append(("inference.py: clean_transactions mentioned", "clean_transactions" in i))

with open('app.py', encoding='utf-8') as f:
    a = f.read()
checks.append(("app.py: no total_tasks=29", '"total_tasks": 29' not in a))

passed = sum(1 for _, v in checks if v)
for name, result in checks:
    print(f"{'✅' if result else '❌'} {name}")
print(f"\n{passed}/{len(checks)} passed")
