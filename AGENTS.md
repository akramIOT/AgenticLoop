# AGENTS.md

Codex / Claude Code 每次工作：

## Read First

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/goal.md`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/PRD.tex`
7. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
8. `docs/research/{CURRENT}/rqs/RQxx/SPEC.yaml`
9. `docs/research/{CURRENT}/EVIDENCE_GATE.yaml`

## Bootstrap

If RQ-local contracts or `TASK_QUEUE.yaml` are missing, run:
```bash
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once
```

## Continuous Loop


```bash
python3 ~/.claude/skills/research/scripts/update_state.py   --repo . --task-id <TASK_ID> --status done   --commit-hash <HASH> --gate-id <GATE_ID>
```

## Stop Conditions

- STATUS.yaml status is `gate_blocked` or `closed_*`
- PRD core hypothesis is contradicted by evidence
- RESEARCH_DIRECTION.md modification is needed (human approval required)
- All gates complete and closeout done

## Rules

- Run relevant tests if code changes.
- Record terminal/test evidence in run report.
- Do not change research direction without human approval.
- Do not create paper results from unverified artifacts.
- Do not fabricate execution, artifact, benchmark, or paper result.
- Do not create Vn+1 before closeout.
- Git allowed: status, diff, log, add allowed files, commit current task, tag closeout / paper binding.
- Git forbidden unless explicitly authorized: git push, git reset --hard, git clean -fd, git rebase, checkout overwriting user changes, rewrite history, force push, deleting files outside task scope.

## 研究智能体行为契约

1. RQ 先于行动。每个任务必须对应一个研究问题、主张、实验、证据、图表或论文章节。
2. 复现先于提出。在声称新颖性或设计实验之前，搜索已有工作并检查当前仓库。
3. 证据先于写作。除非存在相应的数据、日志、表格或引用，否则不要撰写论文主张。
4. 手术式编辑。只修改当前版本文件夹或声明的目标文件。不要静默重写无关工件。
5. 冲突暴露。如果 PRD、规范、任务、论文或代码不一致，停止并报告冲突，而不是取平均值。
6. 长循环检查点。每个主要阶段之后，写下发生了什么变化、产生了什么证据以及什么仍然受阻。
7. 可见失败。缺失的数据、失败的复现、跳过的实验或无法验证的主张必须明确标记。
8. 确定性工作属于脚本。格式化检查、表格生成、指标计算和文件路由应该脚本化，而不是由 LLM 判断决定。
9. 测试是证据而非装饰。只有通过验证预期科学或系统行为的测试才算数。
10. 约定优于新奇。遵循项目的现有文件夹结构、命名、模板和工件格式，除非明确要求迁移。
