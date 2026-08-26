# V0 复现锁定任务实现计划

> **给执行者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）�?superpowers:executing-plans 逐步实现此计划。步骤使用复选框（`- [ ]`）语法以便跟踪�?

> **执行记录说明�?* 本次落地以各任务下方�?`Status / Completed / Commits` 记录为执行真源；原始步骤复选框保留为计划期 TDD/checklist 模板，不再事后逐项改写�?

**目标�?* �?ResearchOS V0 从“尚未锁定复现项”推进到“相关工�?source dossier、baseline matrix、复现任务、smoke harness �?audit gate 均可执行但不产生 paper claim”的 reproduction-lock 状态�?

**架构�?* 本计划不执行 AgenticLoop 主实验，不承认任�?AgenticLoop 有效�?claim。实现方案是先建立可机读�?V0 复现候选清单与基线卡片，再�?P0/P1 相关工作生成最�?smoke 复现合同、测试验证器和审计报告，最后把状态同步到 `TASK_QUEUE.yaml` / `BASELINE_LOCK.yaml` / `REPRODUCTION_PLAN.md` / wiki。所有复现输出只能支�?baseline comparability �?feasibility classification，不能支持论文性能结论�?

**技术栈�?* Python 3 标准库、PyYAML、pytest、git、GitHub HTTPS/SSH source references、AgenticLoop V0 YAML/Markdown 协议�?

**Report 对齐�?*
- **对应章节�?* `docs/research/V0/PRD.tex` �?4 章“基准与复现计划”、第 10 章“实验设计”、第 11 章“任务图与学生工作计划”、第 12 章“Harness 与验收标准”�?
- **证据层：** 本计划产生的脚本、测试和本地复现任务状态属�?`repo-observed fact`；外部论�?仓库链接属于 `source claim`；复现优先级判断属于 `design intent`；smoke 结果不得支持 paper claim�?
- **状态追踪：** 完成后更�?`docs/research/V0/TASK_QUEUE.yaml`、`docs/research/V0/BASELINE_LOCK.yaml`、`docs/research/V0/reproduction/REPRODUCTION_PLAN.md`、`docs/research/V0/reproduction/REPRODUCTION_LEDGER.yaml`、`docs/research/V0/wiki/baseline_landscape.md`、`docs/research/V0/wiki/evidence_map.md`、`docs/research/V0/LOOP_LOG.md`�?

**Report 对齐检查：**
- **Scope match:** 当前 V0 �?`reproduction_lock`，只允许 source/baseline/task-suite/audit-rubric lock；本计划不进�?G3 controlled runs、不执行 AgenticLoop full protocol、不�?paper binding�?
- **Risk coverage:** 已覆�?baseline unfairness、AI Scientist-v2 sandbox 风险、closed-source AlphaEvolve 不可复现、provenance baseline �?claim-gate 不可比、mock/smoke leakage、double-anonymous source 暴露风险�?
- **Evidence layer consistency:** source dossier �?baseline cards 只提�?`source claim`；本地脚本与 smoke harness 通过后才�?`repo-observed fact`；所�?AgenticLoop 效果�?claim 仍保�?`planned`�?
- **Report update completeness:** 计划末尾包含进度文件与风�?下一步文件的更新步骤�?

**依赖关系图：**

```text
任务 1 ──�?任务 2 ──�?任务 4 ──�?任务 5 ──�?任务 6
  �?          �?          �?
  �?          └──�?任务 3 �?
  └────────────────────────�?任务 7
```

---

## 文件结构

- 创建：`tests/agenticloop/test_reproduction_registry.py`  
  责任：验�?V0 复现 registry、baseline cards、reproduction plan �?evidence gate 的结构一致性�?

- 创建：`experiments/agenticloop/scripts/reproduction_registry.py`  
  责任：读取并验证 `docs/research/V0/reproduction/reproduction_targets.yaml`，提供纯函数接口给测试与后续 CLI 使用�?

- 创建：`docs/research/V0/reproduction/reproduction_targets.yaml`  
  责任：登�?V0 相关工作复现目标、优先级、source refs、复现模式、claim boundary �?sandbox 风险�?

- 创建：`docs/research/V0/baselines/B01_ADHOC_AGENT/BASELINE_CARD.yaml`  
  责任：定�?ad-hoc prompting baseline 的公平比较边界�?

- 创建：`docs/research/V0/baselines/B02_AGENT_LABORATORY/BASELINE_CARD.yaml`  
  责任：定�?Agent Laboratory 线�?research-agent baseline �?source �?smoke 复现边界�?

- 创建：`docs/research/V0/baselines/B02_AI_SCIENTIST_V2/BASELINE_CARD.yaml`  
  责任：定�?AI Scientist-v2 强相邻系统的 sandbox smoke �?blocker classification�?

- 创建：`docs/research/V0/baselines/B03_PROVENANCE_ONLY/BASELINE_CARD.yaml`  
  责任：定�?MLflow/DVC provenance-only baseline，明确其不管�?paper claim admission�?

- 创建：`docs/research/V0/baselines/B04_STORM_GROUNDED_WRITING/BASELINE_CARD.yaml`  
  责任：定�?STORM grounded-writing control，验�?citation/outline 不等�?experiment evidence�?

- 创建：`docs/research/V0/baselines/B05_OPENEVOLVE_EVALUATOR/BASELINE_CARD.yaml`  
  责任：定�?OpenEvolve evaluator-guided coding baseline，仅�?task suite 包含 code optimization 时启用�?

- 修改：`docs/research/V0/baselines/INDEX.yaml`  
  责任：汇�?baseline cards，并标注 P0/P1/P2 与是否进�?G2 reproduction lock�?

- 修改：`docs/research/V0/BASELINE_LOCK.yaml`  
  责任：把 selected/candidate baseline 状态从空列表推进为 `needs_human_review` 下的可审计候选矩阵�?

- 修改：`docs/research/V0/reproduction/REPRODUCTION_PLAN.md`  
  责任：写�?V0 复现执行顺序、smoke 命令、blocker 分类与不支持 paper claim 的边界�?

- 修改：`docs/research/V0/reproduction/REPRODUCTION_LEDGER.yaml`  
  责任：登记每个复现目标的状态、证据等级、artifact refs 与是�?claim-support allowed�?

- 修改：`docs/research/V0/TASK_QUEUE.yaml`  
  责任：将 T01/T02/T05 �?V0 复现任务细化为可执行项，同时保持 G3+ blocked�?

- 修改：`docs/research/V0/wiki/baseline_landscape.md`  
  责任：记�?related work 地图与最小可辩护差异�?

- 修改：`docs/research/V0/wiki/evidence_map.md`  
  责任：记�?V0 复现证据层级，说�?smoke/reproduction/source 分别能支持什么�?

---

## 任务分解

### 任务 1: 建立 V0 复现 registry 与结构验证器

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `8a18a30` test(agenticloop): add V0 reproduction target registry; `e259e76` test(agenticloop): tighten V0 registry validation

**Harness（测试框架）:**

- **范围�?* 创建最�?Python 验证器与测试，验�?`reproduction_targets.yaml` �?required fields、priority、reproduction_mode、claim boundary �?source refs。不下载外部仓库，不运行任何 related work�?
- **前置条件�?* 当前分支�?`main`；工作树无未提交的非本任务变更；`docs/research/V0/reproduction/REPRODUCTION_PLAN.md` 存在�?
- **测试入口�?* `pytest tests/agenticloop/test_reproduction_registry.py -v`
- **通过标准�?* 6 个测试通过�? 失败；测试覆盖字段完整性、优先级枚举、source refs 非空、claim_support_allowed 禁止、P0 至少包含 Agent Laboratory / AI Scientist-v2 / provenance-only�?
- **失败恢复�?* `git reset --hard HEAD~1`
- **依赖�?* 无�?
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`tests/agenticloop/test_reproduction_registry.py`
- 创建：`experiments/agenticloop/scripts/reproduction_registry.py`
- 创建：`docs/research/V0/reproduction/reproduction_targets.yaml`

**行为清单（Behavior List�?**

- [ ] 行为 1: registry 拒绝缺少 `target_id`、`priority`、`source_refs`、`reproduction_mode`、`claim_support_allowed` 任一字段的目标�?
- [ ] 行为 2: registry 只接�?`P0`、`P1`、`P2` 三种 priority�?
- [ ] 行为 3: registry 只接�?`official_code_smoke`、`paper_based_adaptation`、`conceptual_control`、`source_dossier_only`、`blocked_closed_source` 五种 reproduction mode�?
- [ ] 行为 4: 所�?V0 target �?`claim_support_allowed` 必须�?`false`�?
- [ ] 行为 5: P0 target 必须至少包含 `AGENT_LABORATORY`、`AI_SCIENTIST_V2`、`PROVENANCE_ONLY`�?
- [ ] 行为 6: 每个 `source_refs` 至少包含一�?URL 字符串，并且不能是空白�?

**接口合同（Interface Contract�?**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Priority = Literal["P0", "P1", "P2"]
ReproductionMode = Literal[
    "official_code_smoke",
    "paper_based_adaptation",
    "conceptual_control",
    "source_dossier_only",
    "blocked_closed_source",
]

@dataclass(frozen=True, slots=True)
class ReproductionTarget:
    target_id: str
    priority: Priority
    related_work: str
    baseline_role: str
    source_refs: tuple[str, ...]
    reproduction_mode: ReproductionMode
    smoke_command: str | None
    blocker_policy: str
    claim_support_allowed: bool

def load_reproduction_targets(path: Path) -> list[ReproductionTarget]:
    """读取 YAML 并返回经过验证的复现目标列表�?""

def validate_reproduction_targets(targets: list[ReproductionTarget]) -> list[str]:
    """返回结构错误列表；空列表表示通过�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_reproduction_registry.py` 写入完整测试�?

```python
from pathlib import Path

import pytest
import yaml

from experiments.agenticloop.scripts.reproduction_registry import (
    ReproductionTarget,
    load_reproduction_targets,
    validate_reproduction_targets,
)


def write_registry(tmp_path: Path, targets: list[dict]) -> Path:
    path = tmp_path / "reproduction_targets.yaml"
    path.write_text(yaml.safe_dump({"schema_version": 1, "targets": targets}, allow_unicode=True), encoding="utf-8")
    return path


def valid_target(**overrides):
    payload = {
        "target_id": "AGENT_LABORATORY",
        "priority": "P0",
        "related_work": "Agent Laboratory",
        "baseline_role": "linear research-agent baseline",
        "source_refs": ["https://github.com/SamuelSchmidgall/AgentLaboratory"],
        "reproduction_mode": "official_code_smoke",
        "smoke_command": "python -m pytest tests/agenticloop/test_reproduction_registry.py -v",
        "blocker_policy": "若官方流程无法在沙箱中运行，则记�?blocked_missing_environment�?,
        "claim_support_allowed": False,
    }
    payload.update(overrides)
    return payload


def test_load_reproduction_targets_returns_dataclass_instances(tmp_path):
    path = write_registry(tmp_path, [valid_target()])
    targets = load_reproduction_targets(path)
    assert targets == [
        ReproductionTarget(
            target_id="AGENT_LABORATORY",
            priority="P0",
            related_work="Agent Laboratory",
            baseline_role="linear research-agent baseline",
            source_refs=("https://github.com/SamuelSchmidgall/AgentLaboratory",),
            reproduction_mode="official_code_smoke",
            smoke_command="python -m pytest tests/agenticloop/test_reproduction_registry.py -v",
            blocker_policy="若官方流程无法在沙箱中运行，则记�?blocked_missing_environment�?,
            claim_support_allowed=False,
        )
    ]


@pytest.mark.parametrize("field", ["target_id", "priority", "source_refs", "reproduction_mode", "claim_support_allowed"])
def test_validate_rejects_missing_required_fields(tmp_path, field):
    target = valid_target()
    target.pop(field)
    path = write_registry(tmp_path, [target])
    with pytest.raises(ValueError, match=field):
        load_reproduction_targets(path)


def test_validate_rejects_unknown_priority(tmp_path):
    path = write_registry(tmp_path, [valid_target(priority="P9")])
    with pytest.raises(ValueError, match="priority"):
        load_reproduction_targets(path)


def test_validate_rejects_unknown_reproduction_mode(tmp_path):
    path = write_registry(tmp_path, [valid_target(reproduction_mode="full_experiment")])
    with pytest.raises(ValueError, match="reproduction_mode"):
        load_reproduction_targets(path)


def test_validate_rejects_claim_supporting_v0_targets(tmp_path):
    path = write_registry(tmp_path, [valid_target(claim_support_allowed=True)])
    with pytest.raises(ValueError, match="claim_support_allowed"):
        load_reproduction_targets(path)


def test_validate_requires_p0_core_targets():
    targets = [
        ReproductionTarget("AGENT_LABORATORY", "P0", "Agent Laboratory", "linear", ("https://example.com/a",), "official_code_smoke", None, "记录 blocker�?, False),
        ReproductionTarget("AI_SCIENTIST_V2", "P0", "AI Scientist-v2", "strong adjacent", ("https://example.com/b",), "official_code_smoke", None, "必须沙箱�?, False),
        ReproductionTarget("PROVENANCE_ONLY", "P0", "MLflow/DVC", "provenance control", ("https://example.com/c",), "conceptual_control", None, "只支�?provenance�?, False),
    ]
    assert validate_reproduction_targets(targets) == []
```

运行：`pytest tests/agenticloop/test_reproduction_registry.py -v`  
预期：FAIL，提�?`ModuleNotFoundError: No module named 'experiments.agenticloop.scripts.reproduction_registry'`�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

**必须确认�?*
- 测试确实失败�?
- 失败原因是模块或函数缺失，不�?YAML 语法错误或测试拼写错误�?
- 测试覆盖�?V0 复现 registry 的关键边界�?

- [ ] **步骤 3：编写最小实�?* (Green)

> **原则：Plan 不提供实现代码�?* 执行者根据接口合同实�?`ReproductionTarget`、`load_reproduction_targets`、`validate_reproduction_targets`，并创建最�?`reproduction_targets.yaml`�? 
> `reproduction_targets.yaml` 必须包含以下 target：`AGENT_LABORATORY`、`AI_SCIENTIST_V2`、`PROVENANCE_ONLY`、`STORM_GROUNDED_WRITING`、`PAPERQA2_LITERATURE_RAG`、`OPENEVOLVE_EVALUATOR`、`ALPHAEVOLVE_OFFICIAL`�?

运行：`pytest tests/agenticloop/test_reproduction_registry.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行测试确认通过** (Green)

运行�?

```bash
pytest tests/agenticloop/test_reproduction_registry.py -v
python3 - <<'PY'
from pathlib import Path
import yaml
for path in Path("docs/research/V0/reproduction").glob("*.yaml"):
    list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
print("V0 reproduction YAML parse OK")
PY
```

预期：测试通过，并输出 `V0 reproduction YAML parse OK`�?

- [ ] **步骤 5：提交代�?*

```bash
git add tests/agenticloop/test_reproduction_registry.py experiments/agenticloop/scripts/reproduction_registry.py docs/research/V0/reproduction/reproduction_targets.yaml
git commit -m "test(agenticloop): add V0 reproduction target registry"
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] 每个行为清单项都有测试覆盖�?
- [ ] 接口签名与合同一致�?
- [ ] 没有下载外部仓库�?
- [ ] 所�?target �?`claim_support_allowed` �?`false`�?
- [ ] `ALPHAEVOLVE_OFFICIAL` �?`reproduction_mode` �?`blocked_closed_source` �?`source_dossier_only`，不得进�?G2 可运�?baseline�?

---

### 任务 2: 生成 baseline cards �?source dossier

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `98bc1ef` docs(research): lock V0 related-work baseline cards

**Harness（测试框架）:**

- **范围�?* �?P0/P1/P2 related work 创建 baseline cards �?source dossier，并验证每张卡都�?role、source refs、reproduction feasibility、claim boundary。不执行任何 smoke command�?
- **前置条件�?* 任务 1 已提交；`reproduction_targets.yaml` 可通过 registry 验证�?
- **测试入口�?* `pytest tests/agenticloop/test_baseline_cards.py -v`
- **通过标准�?* 7 个测试通过�? 失败；所�?baseline cards �?`baselines/INDEX.yaml` 引用；P0 cards �?`BASELINE_LOCK.yaml` candidate baselines 一致�?
- **失败恢复�?* `git reset --hard HEAD~1`
- **依赖�?* 任务 1�?
- **证据层：** `source claim` + `design intent`

**文件:**

- 创建：`tests/agenticloop/test_baseline_cards.py`
- 创建：`docs/research/V0/baselines/B02_AGENT_LABORATORY/BASELINE_CARD.yaml`
- 创建：`docs/research/V0/baselines/B02_AI_SCIENTIST_V2/BASELINE_CARD.yaml`
- 创建：`docs/research/V0/baselines/B03_PROVENANCE_ONLY/BASELINE_CARD.yaml`
- 创建：`docs/research/V0/baselines/B04_STORM_GROUNDED_WRITING/BASELINE_CARD.yaml`
- 创建：`docs/research/V0/baselines/B04_PAPERQA2_LITERATURE_RAG/BASELINE_CARD.yaml`
- 创建：`docs/research/V0/baselines/B05_OPENEVOLVE_EVALUATOR/BASELINE_CARD.yaml`
- 修改：`docs/research/V0/baselines/INDEX.yaml`
- 修改：`docs/research/V0/BASELINE_LOCK.yaml`
- 修改：`docs/research/V0/search/candidate_baselines.yaml`
- 修改：`docs/research/V0/search/search_report.md`

**行为清单（Behavior List�?**

- [ ] 行为 1: 每张 baseline card 包含 `baseline_id`、`related_work`、`priority`、`source_refs`、`role_in_researchos_eval`、`reproduction_feasibility`、`claim_boundary`�?
- [ ] 行为 2: `baselines/INDEX.yaml` 引用�?card 文件全部存在�?
- [ ] 行为 3: `BASELINE_LOCK.yaml` �?P0 baseline 包含 Agent Laboratory、AI Scientist-v2、provenance-only control�?
- [ ] 行为 4: AI Scientist-v2 card 明确要求 sandbox，且不得默认 full run�?
- [ ] 行为 5: AlphaEvolve official 若出现，只能�?source dossier �?closed-source blocker�?
- [ ] 行为 6: STORM/PaperQA2 被标记为 writing/literature control，不得标记为 experimental research-agent baseline�?
- [ ] 行为 7: 所�?card �?`paper_claim_support_allowed` �?`false`�?

**接口合同（Interface Contract�?**

```python
from pathlib import Path
from typing import Any

def load_yaml(path: Path) -> dict[str, Any]:
    """读取单文�?YAML�?""

def collect_baseline_cards(index_path: Path) -> list[Path]:
    """�?baselines/INDEX.yaml 收集 BASELINE_CARD.yaml 路径�?""

def validate_baseline_card(path: Path) -> list[str]:
    """返回单张 baseline card 的结构错误列表�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_baseline_cards.py` 写入完整测试�?

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASELINES = ROOT / "docs/research/V0/baselines"
BASELINE_LOCK = ROOT / "docs/research/V0/BASELINE_LOCK.yaml"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def card_paths():
    index = load_yaml(BASELINES / "INDEX.yaml")
    return [ROOT / entry["card_ref"] for entry in index["baselines"]]


def test_baseline_index_references_existing_cards():
    paths = card_paths()
    assert paths
    for path in paths:
        assert path.exists(), path


def test_each_baseline_card_has_required_fields():
    required = {
        "baseline_id",
        "related_work",
        "priority",
        "source_refs",
        "role_in_researchos_eval",
        "reproduction_feasibility",
        "claim_boundary",
        "paper_claim_support_allowed",
    }
    for path in card_paths():
        card = load_yaml(path)
        assert required <= set(card), path
        assert card["paper_claim_support_allowed"] is False
        assert card["source_refs"], path


def test_baseline_lock_contains_p0_core_candidates():
    lock = load_yaml(BASELINE_LOCK)
    ids = {item["baseline_id"] for item in lock["candidate_baselines"]}
    assert {"B02_AGENT_LABORATORY", "B02_AI_SCIENTIST_V2", "B03_PROVENANCE_ONLY"} <= ids


def test_ai_scientist_v2_requires_sandbox_and_blocks_default_full_run():
    card = load_yaml(BASELINES / "B02_AI_SCIENTIST_V2/BASELINE_CARD.yaml")
    assert card["reproduction_feasibility"]["sandbox_required"] is True
    assert card["reproduction_feasibility"]["default_full_run_allowed"] is False


def test_writing_controls_are_not_experimental_research_agent_baselines():
    for baseline_id in ["B04_STORM_GROUNDED_WRITING", "B04_PAPERQA2_LITERATURE_RAG"]:
        card = load_yaml(BASELINES / baseline_id / "BASELINE_CARD.yaml")
        assert card["role_in_researchos_eval"] in {"grounded_writing_control", "literature_rag_control"}
        assert card["claim_boundary"]["supports_experimental_claim"] is False


def test_openevolve_is_conditional_on_code_optimization_task_suite():
    card = load_yaml(BASELINES / "B05_OPENEVOLVE_EVALUATOR/BASELINE_CARD.yaml")
    assert card["activation_condition"] == "only_if_task_suite_contains_code_optimization"


def test_alphaevolve_official_is_not_a_runnable_v0_baseline_if_recorded():
    alpha_path = BASELINES / "P2_ALPHAEVOLVE_OFFICIAL/BASELINE_CARD.yaml"
    if alpha_path.exists():
        card = load_yaml(alpha_path)
        assert card["reproduction_feasibility"]["status"] in {"source_dossier_only", "blocked_closed_source"}
        assert card["paper_claim_support_allowed"] is False
```

运行：`pytest tests/agenticloop/test_baseline_cards.py -v`  
预期：FAIL，提�?baseline card �?index 字段缺失�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

确认失败来自 card/index 尚未创建，而不�?YAML 语法错误�?

- [ ] **步骤 3：编写最小实�?* (Green)

根据行为清单创建 baseline cards。source refs 必须至少包含�?

- Agent Laboratory: `https://github.com/SamuelSchmidgall/AgentLaboratory` �?`https://arxiv.org/abs/2501.04227`
- AI Scientist-v2: `https://github.com/SakanaAI/AI-Scientist-v2` �?`https://arxiv.org/abs/2504.08066`
- MLflow: `https://mlflow.org/docs/latest/`
- DVC: `https://dvc.org/doc`
- STORM: `https://github.com/stanford-oval/storm` �?`https://storm-project.stanford.edu/research/storm/`
- PaperQA2: `https://github.com/Future-House/paper-qa` �?`https://arxiv.org/abs/2312.07559`
- OpenEvolve: `https://github.com/algorithmicsuperintelligence/openevolve`
- AlphaEvolve official: `https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/`

运行：`pytest tests/agenticloop/test_baseline_cards.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行测试确认通过** (Green)

运行�?

```bash
pytest tests/agenticloop/test_reproduction_registry.py tests/agenticloop/test_baseline_cards.py -v
python3 - <<'PY'
from pathlib import Path
import yaml
for path in Path("docs/research/V0/baselines").rglob("*.yaml"):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("baseline cards YAML parse OK")
PY
```

预期：全部通过，并输出 `baseline cards YAML parse OK`�?

- [ ] **步骤 5：提交代�?*

```bash
git add tests/agenticloop/test_baseline_cards.py docs/research/V0/baselines docs/research/V0/BASELINE_LOCK.yaml docs/research/V0/search/candidate_baselines.yaml docs/research/V0/search/search_report.md
git commit -m "docs(research): lock V0 related-work baseline cards"
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] P0/P1/P2 优先级与 V0 reproduction-lock 边界一致�?
- [ ] AI Scientist-v2 没有被默认标记为 full runnable baseline�?
- [ ] STORM/PaperQA2 没有被误写成实验执行 baseline�?
- [ ] 所�?source refs 为真�?URL�?
- [ ] 所�?paper-facing claim 均保�?forbidden/draft�?

---

### 任务 3: 编写 P0 smoke 复现合同与本�?dry-run harness

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `0c29726` feat(agenticloop): add dry-run smoke contracts for P0 reproductions

**Harness（测试框架）:**

- **范围�?* �?Agent Laboratory、AI Scientist-v2、provenance-only control 创建 smoke reproduction spec �?dry-run 命令生成器。dry-run 只验证命令、目录、日�?schema，不克隆、不安装、不调用外部模型�?
- **前置条件�?* 任务 1 已提交；任务 2 可并行但完成后需一起进入任�?4�?
- **测试入口�?* `pytest tests/agenticloop/test_smoke_harness_contract.py -v`
- **通过标准�?* 5 个测试通过�? 失败；dry-run artifact schema 包含 command、cwd、env、expected_outputs、blocker_policy、claim_support_allowed=false�?
- **失败恢复�?* `git reset --hard HEAD~1`
- **依赖�?* 任务 1�?
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`tests/agenticloop/test_smoke_harness_contract.py`
- 创建：`experiments/agenticloop/scripts/smoke_harness.py`
- 创建：`docs/research/V0/reproduction/smoke_specs/AGENT_LABORATORY.yaml`
- 创建：`docs/research/V0/reproduction/smoke_specs/AI_SCIENTIST_V2.yaml`
- 创建：`docs/research/V0/reproduction/smoke_specs/PROVENANCE_ONLY.yaml`

**行为清单（Behavior List�?**

- [ ] 行为 1: smoke spec 必须声明 `dry_run_only: true`�?
- [ ] 行为 2: smoke spec 必须声明 `claim_support_allowed: false`�?
- [ ] 行为 3: AI Scientist-v2 spec 必须声明 sandbox required�?
- [ ] 行为 4: provenance-only spec 必须声明其不管理 paper claim admission�?
- [ ] 行为 5: dry-run harness 能为每个 P0 target 生成 run report skeleton，且 report 明确 `is_mock: true`�?

**接口合同（Interface Contract�?**

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class SmokeSpec:
    target_id: str
    dry_run_only: bool
    sandbox_required: bool
    command: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    blocker_policy: str
    claim_support_allowed: bool

def load_smoke_spec(path: Path) -> SmokeSpec:
    """读取并验证单�?smoke spec�?""

def build_dry_run_report(spec: SmokeSpec, repo_root: Path) -> dict:
    """返回不执行外部命令的 run report skeleton�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_smoke_harness_contract.py` 写入完整测试�?

```python
from pathlib import Path

from experiments.agenticloop.scripts.smoke_harness import build_dry_run_report, load_smoke_spec


ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "docs/research/V0/reproduction/smoke_specs"


def test_p0_smoke_specs_exist():
    for target_id in ["AGENT_LABORATORY", "AI_SCIENTIST_V2", "PROVENANCE_ONLY"]:
        assert (SPEC_DIR / f"{target_id}.yaml").exists()


def test_smoke_specs_are_dry_run_and_not_claim_supporting():
    for path in SPEC_DIR.glob("*.yaml"):
        spec = load_smoke_spec(path)
        assert spec.dry_run_only is True
        assert spec.claim_support_allowed is False


def test_ai_scientist_v2_requires_sandbox():
    spec = load_smoke_spec(SPEC_DIR / "AI_SCIENTIST_V2.yaml")
    assert spec.sandbox_required is True


def test_provenance_only_declares_claim_admission_gap():
    spec = load_smoke_spec(SPEC_DIR / "PROVENANCE_ONLY.yaml")
    assert "不管�?paper claim admission" in spec.blocker_policy


def test_dry_run_report_marks_mock_and_forbids_claim_support():
    spec = load_smoke_spec(SPEC_DIR / "AGENT_LABORATORY.yaml")
    report = build_dry_run_report(spec, ROOT)
    assert report["target_id"] == "AGENT_LABORATORY"
    assert report["is_mock"] is True
    assert report["claim_support_allowed"] is False
    assert report["command"]
    assert report["expected_outputs"]
```

运行：`pytest tests/agenticloop/test_smoke_harness_contract.py -v`  
预期：FAIL，提�?`smoke_harness` 模块�?smoke spec 文件不存在�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

确认失败来自模块/spec 缺失，不是测试路径错误�?

- [ ] **步骤 3：编写最小实�?* (Green)

创建 `smoke_harness.py` 与三�?P0 smoke specs。命令必须是 dry-run 形式，例�?`python experiments/agenticloop/scripts/smoke_harness.py --target AGENT_LABORATORY --dry-run`，不得触发真�?clone/install/API call�?

运行：`pytest tests/agenticloop/test_smoke_harness_contract.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行测试确认通过** (Green)

运行�?

```bash
pytest tests/agenticloop/test_reproduction_registry.py tests/agenticloop/test_smoke_harness_contract.py -v
```

预期：全部通过�?

- [ ] **步骤 5：提交代�?*

```bash
git add tests/agenticloop/test_smoke_harness_contract.py experiments/agenticloop/scripts/smoke_harness.py docs/research/V0/reproduction/smoke_specs
git commit -m "feat(agenticloop): add dry-run smoke contracts for P0 reproductions"
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] dry-run 没有下载或执行外部代码�?
- [ ] 所�?generated report skeleton 都标�?`is_mock: true`�?
- [ ] smoke 输出没有进入 `PAPER_CLAIM_LEDGER.yaml` �?allowed claim�?
- [ ] AI Scientist-v2 sandbox 风险明确�?

---

### 任务 4: 更新 V0 复现计划、ledger 与任务队�?

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `bca4f66` docs(research): materialize V0 reproduction lock tasks

**Harness（测试框架）:**

- **范围�?* 把任�?1-3 �?registry/card/smoke specs 写入 AgenticLoop V0 真源：`REPRODUCTION_PLAN.md`、`REPRODUCTION_LEDGER.yaml`、`TASK_QUEUE.yaml`、`AUDIT_QUEUE.yaml`。不执行外部复现�?
- **前置条件�?* 任务 1、任�?2、任�?3 已提交�?
- **测试入口�?* `pytest tests/agenticloop/test_v0_reproduction_state.py -v`
- **通过标准�?* 6 个测试通过�? 失败；T05 展开�?P0 reproduction subtasks；G3+ 仍为 blocked；ledger 中无 claim-supporting smoke evidence�?
- **失败恢复�?* `git reset --hard HEAD~1`
- **依赖�?* 任务 1、任�?2、任�?3�?
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`tests/agenticloop/test_v0_reproduction_state.py`
- 修改：`docs/research/V0/reproduction/REPRODUCTION_PLAN.md`
- 修改：`docs/research/V0/reproduction/REPRODUCTION_LEDGER.yaml`
- 修改：`docs/research/V0/reproduction/REPRODUCTION_INDEX.yaml`
- 修改：`docs/research/V0/TASK_QUEUE.yaml`
- 修改：`docs/research/V0/AUDIT_QUEUE.yaml`

**行为清单（Behavior List�?**

- [ ] 行为 1: `REPRODUCTION_PLAN.md` 明确列出 P0 执行顺序：Agent Laboratory dry-run/smoke、AI Scientist-v2 sandbox smoke/blocker、provenance-only control�?
- [ ] 行为 2: `REPRODUCTION_LEDGER.yaml` 中每�?P0 target �?`paper_claim_support_allowed` �?`false`�?
- [ ] 行为 3: `TASK_QUEUE.yaml` �?T05 包含 P0 reproduction subtasks�?
- [ ] 行为 4: `TASK_QUEUE.yaml` �?G3/G4/G5/G6/G7 仍为 blocked�?
- [ ] 行为 5: `AUDIT_QUEUE.yaml` 包含 G2 reproduction audit�?
- [ ] 行为 6: `REPRODUCTION_INDEX.yaml` 能解析每�?target �?spec/card/ledger ref�?

**接口合同（Interface Contract�?**

```python
from pathlib import Path
from typing import Any

def load_yaml(path: Path) -> dict[str, Any]:
    """读取单文�?YAML�?""

def task_queue_contains_reproduction_subtasks(task_queue: dict[str, Any], expected_ids: set[str]) -> bool:
    """检�?T05 是否包含 expected_ids 对应的复现子任务�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_v0_reproduction_state.py` 写入完整测试�?

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
V0 = ROOT / "docs/research/V0"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_reproduction_plan_lists_p0_execution_order():
    text = (V0 / "reproduction/REPRODUCTION_PLAN.md").read_text(encoding="utf-8")
    assert "AGENT_LABORATORY" in text
    assert "AI_SCIENTIST_V2" in text
    assert "PROVENANCE_ONLY" in text
    assert text.index("AGENT_LABORATORY") < text.index("AI_SCIENTIST_V2") < text.index("PROVENANCE_ONLY")


def test_reproduction_ledger_forbids_paper_claim_support_for_p0():
    ledger = load_yaml(V0 / "reproduction/REPRODUCTION_LEDGER.yaml")
    assets = {item["target_id"]: item for item in ledger["assets"]}
    for target_id in ["AGENT_LABORATORY", "AI_SCIENTIST_V2", "PROVENANCE_ONLY"]:
        assert assets[target_id]["paper_claim_support_allowed"] is False


def test_task_queue_expands_t05_reproduction_subtasks():
    queue = load_yaml(V0 / "TASK_QUEUE.yaml")
    task = next(item for item in queue["tasks"] if item["id"] == "T05")
    subtask_ids = {item["id"] for item in task["subtasks"]}
    assert {"T05_AGENT_LABORATORY", "T05_AI_SCIENTIST_V2", "T05_PROVENANCE_ONLY"} <= subtask_ids


def test_later_gates_remain_blocked():
    queue = load_yaml(V0 / "TASK_QUEUE.yaml")
    gates = {item["gate_id"]: item["status"] for item in queue["gates"]}
    for gate_id in ["G3_CONTROLLED_RUNS", "G4_EVIDENCE_AUDIT", "G5_REAL_CASE_STUDY", "G6_SELF_HOSTING", "G7_PAPER_BINDING"]:
        assert gates[gate_id] == "blocked"


def test_audit_queue_contains_g2_reproduction_audit():
    audit = load_yaml(V0 / "AUDIT_QUEUE.yaml")
    audit_ids = {item["audit_id"] for item in audit["audits"]}
    assert "G2_REPRODUCTION_AUDIT" in audit_ids


def test_reproduction_index_resolves_target_refs():
    index = load_yaml(V0 / "reproduction/REPRODUCTION_INDEX.yaml")
    for item in index["targets"]:
        for ref_name in ["card_ref", "smoke_spec_ref", "ledger_ref"]:
            assert (V0 / item[ref_name]).exists(), item
```

运行：`pytest tests/agenticloop/test_v0_reproduction_state.py -v`  
预期：FAIL，提示计划、ledger �?queue 尚未更新�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

确认失败来自状态文件未更新，而不�?YAML 语法错误�?

- [ ] **步骤 3：编写最小实�?* (Green)

更新 AgenticLoop V0 状态文件。T05 subtasks 必须只包�?dry-run/smoke/blocker classification，不得包�?G3 controlled runs�?

运行：`pytest tests/agenticloop/test_v0_reproduction_state.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行测试确认通过** (Green)

运行�?

```bash
pytest tests/agenticloop/test_reproduction_registry.py tests/agenticloop/test_baseline_cards.py tests/agenticloop/test_smoke_harness_contract.py tests/agenticloop/test_v0_reproduction_state.py -v
```

预期：全部通过�?

- [ ] **步骤 5：提交代�?*

```bash
git add tests/agenticloop/test_v0_reproduction_state.py docs/research/V0/reproduction docs/research/V0/TASK_QUEUE.yaml docs/research/V0/AUDIT_QUEUE.yaml
git commit -m "docs(research): materialize V0 reproduction lock tasks"
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] T05 只推�?G2 reproduction lock�?
- [ ] G3+ 保持 blocked�?
- [ ] smoke/dry-run 没有被写�?claim-supporting evidence�?
- [ ] 每个 ledger item 都能解析 card/spec/report ref�?

---

### 任务 5: 实现 source/baseline audit 脚本

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `8bc77eb` feat(agenticloop): add V0 source and reproduction audit

**Harness（测试框架）:**

- **范围�?* 实现 `audit_sources.py`，检�?source refs、baseline cards、reproduction targets、ledger �?anti-mock policy 的一致性。不访问网络，不判断论文真实性，只验证本�?dossier 合规�?
- **前置条件�?* 任务 4 已提交�?
- **测试入口�?* `pytest tests/agenticloop/test_audit_sources.py -v`
- **通过标准�?* 5 个测试通过�? 失败；脚�?CLI 对合规输入返�?0，对 claim-supporting smoke 或缺�?source 返回�?0�?
- **失败恢复�?* `git reset --hard HEAD~1`
- **依赖�?* 任务 4�?
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`tests/agenticloop/test_audit_sources.py`
- 创建：`experiments/agenticloop/scripts/audit_sources.py`
- 修改：`experiments/agenticloop/scripts/README.md`
- 修改：`docs/research/V0/audits/G2_reproduction_audit.yaml`

**行为清单（Behavior List�?**

- [ ] 行为 1: CLI 对当�?V0 dossier 返回 exit code 0�?
- [ ] 行为 2: CLI 在任一 baseline card 缺少 source refs 时返�?exit code 1�?
- [ ] 行为 3: CLI 在任一 smoke/ledger item `paper_claim_support_allowed=true` 时返�?exit code 1�?
- [ ] 行为 4: CLI 输出 JSON audit summary，包�?checked_files、errors、warnings�?
- [ ] 行为 5: `G2_reproduction_audit.yaml` 记录 audit command �?pass criteria�?

**接口合同（Interface Contract�?**

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class AuditResult:
    checked_files: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

def audit_v0_sources(repo_root: Path) -> AuditResult:
    """审计 V0 source/baseline/reproduction dossier 的本地一致性�?""

def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint；成功返�?0，失败返�?1�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_audit_sources.py` 写入完整测试�?

```python
import json
import subprocess
import sys
from pathlib import Path

import yaml

from experiments.agenticloop.scripts.audit_sources import audit_v0_sources


ROOT = Path(__file__).resolve().parents[2]


def test_audit_v0_sources_passes_current_dossier():
    result = audit_v0_sources(ROOT)
    assert result.errors == ()
    assert result.checked_files


def test_cli_outputs_json_summary():
    completed = subprocess.run(
        [sys.executable, "experiments/agenticloop/scripts/audit_sources.py", "--repo", str(ROOT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert set(payload) == {"checked_files", "errors", "warnings"}


def test_audit_rejects_missing_source_refs(tmp_path):
    card_dir = tmp_path / "docs/research/V0/baselines/BAD"
    card_dir.mkdir(parents=True)
    (tmp_path / "docs/research/V0/baselines").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/research/V0/baselines/INDEX.yaml").write_text(
        yaml.safe_dump({"baselines": [{"card_ref": "docs/research/V0/baselines/BAD/BASELINE_CARD.yaml"}]}),
        encoding="utf-8",
    )
    (card_dir / "BASELINE_CARD.yaml").write_text(
        yaml.safe_dump({"baseline_id": "BAD", "paper_claim_support_allowed": False, "source_refs": []}),
        encoding="utf-8",
    )
    result = audit_v0_sources(tmp_path)
    assert any("source_refs" in error for error in result.errors)


def test_audit_rejects_claim_supporting_reproduction_ledger(tmp_path):
    ledger_dir = tmp_path / "docs/research/V0/reproduction"
    ledger_dir.mkdir(parents=True)
    (ledger_dir / "REPRODUCTION_LEDGER.yaml").write_text(
        yaml.safe_dump({"assets": [{"target_id": "BAD", "paper_claim_support_allowed": True}]}),
        encoding="utf-8",
    )
    result = audit_v0_sources(tmp_path)
    assert any("paper_claim_support_allowed" in error for error in result.errors)


def test_g2_reproduction_audit_file_records_command():
    audit_path = ROOT / "docs/research/V0/audits/G2_reproduction_audit.yaml"
    payload = yaml.safe_load(audit_path.read_text(encoding="utf-8"))
    assert payload["audit_id"] == "G2_REPRODUCTION_AUDIT"
    assert "audit_sources.py" in payload["command"]
```

运行：`pytest tests/agenticloop/test_audit_sources.py -v`  
预期：FAIL，提�?`audit_sources.py` �?audit YAML 缺失�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

确认失败来自审计脚本缺失，不是路径误判�?

- [ ] **步骤 3：编写最小实�?* (Green)

实现本地一致性审计。禁止在审计中访问网络；source URL 的真实性由 G0 source dossier 人工/外部搜索审计，不由本脚本判断�?

运行：`pytest tests/agenticloop/test_audit_sources.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行测试确认通过** (Green)

运行�?

```bash
pytest tests/agenticloop -v
python experiments/agenticloop/scripts/audit_sources.py --repo .
```

预期：全部测试通过，CLI 输出 JSON �?`errors` 为空�?

- [ ] **步骤 5：提交代�?*

```bash
git add tests/agenticloop/test_audit_sources.py experiments/agenticloop/scripts/audit_sources.py experiments/agenticloop/scripts/README.md docs/research/V0/audits/G2_reproduction_audit.yaml
git commit -m "feat(agenticloop): add V0 source and reproduction audit"
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] 审计脚本不联网�?
- [ ] 审计脚本不承�?paper claim�?
- [ ] 对缺 source refs �?claim-supporting smoke 能失败�?
- [ ] audit YAML 记录 command、inputs、outputs、pass criteria�?

---

### 任务 6: 更新 wiki、evidence map �?loop log

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `2c3127a` docs(research): record V0 reproduction evidence boundaries

**Harness（测试框架）:**

- **范围�?* �?V0 related work 复现策略写入 wiki �?loop log，明确哪些进�?P0/P1/P2、哪�?blocked、哪些只能作�?source claim。不修改 PRD 结论，不改变 PAPER_CLAIM_LEDGER �?allowed 状态�?
- **前置条件�?* 任务 5 已提交�?
- **测试入口�?* `pytest tests/agenticloop/test_reproduction_docs_boundary.py -v`
- **通过标准�?* 4 个测试通过�? 失败；wiki 包含 baseline landscape、evidence map、blocked policy；claim ledger 中没�?allowed claim�?
- **失败恢复�?* `git reset --hard HEAD~1`
- **依赖�?* 任务 5�?
- **证据层：** `report synthesis`

**文件:**

- 创建：`tests/agenticloop/test_reproduction_docs_boundary.py`
- 修改：`docs/research/V0/wiki/baseline_landscape.md`
- 修改：`docs/research/V0/wiki/evidence_map.md`
- 修改：`docs/research/V0/wiki/failed_paths.md`
- 修改：`docs/research/V0/LOOP_LOG.md`
- 修改：`docs/research/V0/PAPER_CLAIM_LEDGER.yaml`

**行为清单（Behavior List�?**

- [ ] 行为 1: baseline landscape 明确 P0 = Agent Laboratory、AI Scientist-v2、provenance-only�?
- [ ] 行为 2: evidence map 明确 source dossier、dry-run、smoke、full reproduction 的证据等级差异�?
- [ ] 行为 3: failed paths 记录 AlphaEvolve official closed-source �?source-only 边界�?
- [ ] 行为 4: Paper claim ledger 没有任何 `paper_allowed: true`�?

**接口合同（Interface Contract�?**

```python
from pathlib import Path
from typing import Any

def read_text(path: Path) -> str:
    """读取 UTF-8 文本�?""

def load_yaml(path: Path) -> dict[str, Any]:
    """读取单文�?YAML�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_reproduction_docs_boundary.py` 写入完整测试�?

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
V0 = ROOT / "docs/research/V0"


def test_baseline_landscape_names_p0_targets():
    text = (V0 / "wiki/baseline_landscape.md").read_text(encoding="utf-8")
    for token in ["Agent Laboratory", "AI Scientist-v2", "MLflow", "DVC"]:
        assert token in text


def test_evidence_map_distinguishes_source_smoke_and_full_reproduction():
    text = (V0 / "wiki/evidence_map.md").read_text(encoding="utf-8")
    for token in ["source dossier", "dry-run", "smoke", "full reproduction"]:
        assert token in text
    assert "smoke 不支�?paper claim" in text


def test_failed_paths_records_alphaevolve_boundary():
    text = (V0 / "wiki/failed_paths.md").read_text(encoding="utf-8")
    assert "AlphaEvolve" in text
    assert "closed-source" in text or "source-only" in text


def test_no_paper_claim_allowed_after_v0_reproduction_lock():
    ledger = yaml.safe_load((V0 / "PAPER_CLAIM_LEDGER.yaml").read_text(encoding="utf-8"))
    assert all(item["paper_allowed"] is False for item in ledger["claims"])
```

运行：`pytest tests/agenticloop/test_reproduction_docs_boundary.py -v`  
预期：FAIL，提�?wiki 文本尚未包含目标边界�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

确认失败来自文档边界尚未写入，而不�?claim ledger YAML 错误�?

- [ ] **步骤 3：编写最小实�?* (Green)

更新 wiki �?loop log。`PAPER_CLAIM_LEDGER.yaml` 只允许补充说明，不允许把任何 planned claim 改为 allowed�?

运行：`pytest tests/agenticloop/test_reproduction_docs_boundary.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行测试确认通过** (Green)

运行�?

```bash
pytest tests/agenticloop -v
python experiments/agenticloop/scripts/audit_sources.py --repo .
```

预期：全部通过�?

- [ ] **步骤 5：提交代�?*

```bash
git add tests/agenticloop/test_reproduction_docs_boundary.py docs/research/V0/wiki docs/research/V0/LOOP_LOG.md docs/research/V0/PAPER_CLAIM_LEDGER.yaml
git commit -m "docs(research): record V0 reproduction evidence boundaries"
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] wiki 没有�?source claim 写成 observed result�?
- [ ] smoke 不支�?paper claim 的边界清楚�?
- [ ] AlphaEvolve official 的不可复现边界清楚�?
- [ ] Paper claim ledger 仍没�?allowed claim�?

---

### 任务 7: 最终校验、状态同步与远端推�?

**Status:** �?COMPLETE
**Completed:** 2026-05-19
**Commits:** `89c4fcf` chore(research): verify V0 reproduction lock state; `e9f1c1d` docs(research): sync V0 state verification log

**Harness（测试框架）:**

- **范围�?* 运行全量 V0 复现锁定测试、AgenticLoop validator、YAML parse、git diff check，并推送到 private GitHub。只同步状态，不执�?G3+ 主实验�?
- **前置条件�?* 任务 1-6 已提交�?
- **测试入口�?* `pytest tests/agenticloop -v`
- **通过标准�?* `tests/agenticloop` 全通过；`audit_sources.py` 返回 0；YAML 全解析通过；`prd-ready` 只允许因 `PRD_STATUS: HUMAN_APPROVED` 缺失�?blocked；git 工作树干净；远�?`origin/main` 更新�?
- **失败恢复�?* 若最后一个提交有问题，使�?`git revert HEAD`，不得使�?`git reset --hard` 删除他人变更�?
- **依赖�?* 任务 1-6�?
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`docs/research/V0/STATUS.yaml`
- 修改：`docs/research/V0/GIT_STATE.yaml`
- 修改：`docs/research/V0/git_log.md`

**行为清单（Behavior List�?**

- [ ] 行为 1: `tests/agenticloop` 全部通过�?
- [ ] 行为 2: `audit_sources.py --repo .` 返回 0�?
- [ ] 行为 3: YAML 全仓解析通过�?
- [ ] 行为 4: `prd-ready` 的唯一 blocker �?human approval，而不�?missing benchmark/source/rubric�?
- [ ] 行为 5: `STATUS.yaml` 当前 gate 仍是 G0/G1/G2 相关状态，不得进入 G3�?
- [ ] 行为 6: `git_log.md` 记录每个任务 commit�?

**接口合同（Interface Contract�?**

```python
from pathlib import Path

def parse_git_log(path: Path) -> list[str]:
    """读取 git_log.md 中记录的 commit sha�?""
```

- [ ] **步骤 1：编写失败的测试** (Red)

�?`tests/agenticloop/test_final_v0_reproduction_gate.py` 写入完整测试�?

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
V0 = ROOT / "docs/research/V0"


def test_status_does_not_enter_controlled_runs():
    status = yaml.safe_load((V0 / "STATUS.yaml").read_text(encoding="utf-8"))
    assert status["current_gate"] in {"G0_SEARCH_LOCK", "G1_TASK_SUITE_LOCK", "G2_REPRODUCTION_LOCK"}
    assert status["paper_binding"]["allowed"] is False


def test_git_log_records_v0_reproduction_commits():
    text = (V0 / "git_log.md").read_text(encoding="utf-8")
    for token in [
        "V0 reproduction target registry",
        "related-work baseline cards",
        "dry-run smoke contracts",
        "source and reproduction audit",
    ]:
        assert token in text
```

运行：`pytest tests/agenticloop/test_final_v0_reproduction_gate.py -v`  
预期：FAIL，提示状态或 git log 尚未同步�?

- [ ] **步骤 2：运行测试确认失�?* (Red)

确认失败来自最终状态未同步�?

- [ ] **步骤 3：编写最小实�?* (Green)

更新 `STATUS.yaml`、`GIT_STATE.yaml`、`git_log.md`。状态最多推进到 `gate_blocked` �?G2 reproduction lock 相关状态；不得标记 `closed_stable` �?`paper_binding_ready`�?

运行：`pytest tests/agenticloop/test_final_v0_reproduction_gate.py -v`  
预期：PASS�?

- [ ] **步骤 4：运行全量验�?* (Green)

运行�?

```bash
pytest tests/agenticloop -v
python experiments/agenticloop/scripts/audit_sources.py --repo .
python3 - <<'PY'
from pathlib import Path
import yaml
for path in Path(".").rglob("*.yaml"):
    list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
print("all YAML parse OK")
PY
python3 /home/xyh/.claude/skills/research-spec/scripts/validate_research.py --repo /home/xyh/code/ResearchOS --mode prd-ready
```

预期�?
- `pytest tests/agenticloop -v`: PASS�?
- `audit_sources.py`: exit code 0�?
- YAML parse: 输出 `all YAML parse OK`�?
- `prd-ready`: 允许 blocked，但错误只能�?`PRD_STATUS: HUMAN_APPROVED` 缺失；若出现 source/baseline/rubric 缺口，必须修复�?

- [ ] **步骤 5：提交代码并推�?*

```bash
git add tests/agenticloop/test_final_v0_reproduction_gate.py docs/research/V0/STATUS.yaml docs/research/V0/GIT_STATE.yaml docs/research/V0/git_log.md
git commit -m "chore(research): verify V0 reproduction lock state"
git push origin main
```

- [ ] **步骤 6：验�?spec 合规（自检�?*

- [ ] 没有进入 G3 controlled runs�?
- [ ] 没有 allowed paper claim�?
- [ ] 所�?smoke/dry-run 均标注不支持 paper claim�?
- [ ] 远端 private repo `origin/main` 已包含全部提交�?

---

## Quality Gate

每个任务进入下一任务前必须满足：

- [ ] 当前任务测试全部通过�?
- [ ] `pytest tests/agenticloop -v` 不出现回归�?
- [ ] YAML 文件可解析�?
- [ ] 没有新增未说明的 external execution�?
- [ ] 没有�?mock/smoke/dry-run 写成 claim-supporting evidence�?
- [ ] 代码或文档已提交，commit message 描述清楚�?
- [ ] Spec 合规自检通过�?

---

## Report 进度更新

### 1. 更新进度章节

- [ ] �?`docs/research/V0/TASK_QUEUE.yaml` 中将 T01/T02/T05 的实际状态同步到 source/baseline/reproduction lock 进度�?
- [ ] �?`docs/research/V0/LOOP_LOG.md` 中引用每个任�?commit SHA�?
- [ ] 如实际执行时发现 Agent Laboratory �?AI Scientist-v2 无法 smoke，必须在 `docs/research/V0/wiki/failed_paths.md` �?`REPRODUCTION_LEDGER.yaml` 中记�?blocker，不得删除该失败�?

### 2. 更新风险/下一步章�?

- [ ] �?`docs/research/V0/wiki/open_questions.md` 补充 human decisions：是否把 AI Scientist-v2 作为�?baseline，是否启�?OpenEvolve，是否采�?STORM �?PaperQA2 作为 writing/literature control�?
- [ ] �?`docs/research/V0/wiki/failed_paths.md` 补充风险矩阵�?

```markdown
| 风险 | 概率 | 影响 | 应对 | 兜底 |
| --- | --- | --- | --- | --- |
| AI Scientist-v2 执行 LLM 生成代码导致 sandbox 风险 | �?| �?| 只做 dry-run/sandbox smoke | classify as blocked but informative |
| AlphaEvolve official closed-source 不可复现 | �?| �?| 只做 source dossier | 使用 OpenEvolve 作为 evaluator-guided open baseline |
| Provenance-only baseline �?claim gate 不可�?| �?| �?| 明确 conceptual control 边界 | 只用于反驳“MLflow/DVC 已解决全部问题”的审稿疑问 |
| STORM/PaperQA2 不执行实�?| �?| �?| 标记�?writing/literature control | 不放入主 research-agent baseline |
```

### 3. 证据层标�?

- [ ] 本计划产生的脚本/测试/本地状�?�?`repo-observed fact`�?
- [ ] Baseline 选择理由 �?`design intent`�?
- [ ] 外部论文/仓库链接 �?`source claim`�?
- [ ] dry-run/smoke 输出 �?`plumbing evidence only`，不支持 paper claim�?

### 4. 交叉检�?

- [ ] 进度文件未把未执行复现写成已完成�?
- [ ] 风险章节未遗�?sandbox、closed-source、mock leakage �?claim-boundary 风险�?
- [ ] `PAPER_CLAIM_LEDGER.yaml` 中所�?claim 仍为 `paper_allowed: false`�?

---

## Task Completion Protocol

每个任务完成后：

1. 对照行为清单逐项确认测试覆盖�?
2. 确认接口合同未漂移�?
3. 运行当前任务测试�?`pytest tests/agenticloop -v`�?
4. 提交当前任务�?
5. 在计划文件中把任务标记为完成并记�?commit SHA�?
6. 全部任务完成后，执行统一代码质量审查，重点检�?DRY、YAGNI、AgenticLoop evidence boundary、V0 reproduction-lock 边界与任务状态一致性�?

---

## 自检结果

- **Spec coverage:** 覆盖 source dossier、baseline cards、P0 smoke specs、reproduction ledger、audit script、wiki/evidence map、final gate verification�?
- **Placeholder scan:** 本计划未使用未决占位表达�?
- **Type consistency:** `ReproductionTarget`、`SmokeSpec`、`AuditResult` 在任务间职责分离，未复用冲突字段�?
- **Harness completeness:** 每个任务均包含范围、前置条件、测试入口、通过标准、失败恢复、依赖、证据层�?
- **Atomicity check:** 每个任务只处理一个关注点，可独立提交和回滚�?
- **TDD compliance:** 每个任务均包�?Red、确认失败、Green、确认通过、提交、自检�?
- **Report alignment:** 计划总范围停留在 V0 reproduction-lock，没有越界进�?G3 controlled runs �?paper binding�?
