"""
One-time repository reorganization.

Moves flat root modules into layer packages, rewrites
every import across the repo, adds path shims to moved
root tests, moves docs, deletes dead files.

Run once from repo root:  py tools/reorganize_repo.py
"""

import os
import re
import shutil
import sys

ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
os.chdir(ROOT)

# ======================================================
# Module → package mapping
# ======================================================

MAPPING = {
    # core
    "engine": "core", "bot_state": "core",
    "bot_monitor": "core", "watchdog": "core",
    "day_summary": "core", "startup_banner": "core",
    "tick_cache": "core", "candle_engine": "core",
    "orb_engine": "core", "strategy": "core",
    "historical_data": "core",
    "instrument_loader": "core", "watchlist": "core",
    "master_loader": "core", "system_registry": "core",
    "market_recorder": "core", "market_replay": "core",

    # intelligence
    "brain": "intelligence",
    "brain_context": "intelligence",
    "conviction_engine": "intelligence",
    "evidence": "intelligence",
    "evidence_builder": "intelligence",
    "evidence_validator": "intelligence",
    "intelligence_engine": "intelligence",
    "intelligence_bootstrap": "intelligence",
    "intelligence_context": "intelligence",
    "intelligence_snapshot": "intelligence",
    "institutional_intelligence": "intelligence",
    "sector_engine": "intelligence",
    "sector_strength": "intelligence",
    "industry_engine": "intelligence",
    "theme_engine": "intelligence",
    "theme_dictionary": "intelligence",
    "relative_strength_engine": "intelligence",
    "market_mood_engine": "intelligence",
    "market_environment": "intelligence",
    "market_regime_engine": "intelligence",
    "market_profile": "intelligence",
    "market_pulse_engine": "intelligence",
    "market_memory": "intelligence",
    "pattern_engine": "intelligence",
    "company_intelligence": "intelligence",
    "event_intelligence": "intelligence",
    "causal_knowledge": "intelligence",
    "causal_reasoning_engine": "intelligence",
    "knowledge_graph": "intelligence",
    "fno_opportunity_engine": "intelligence",
    "opportunity_pool_engine": "intelligence",
    "opportunity_ranker": "intelligence",
    "results_engine": "intelligence",
    "results_calendar": "intelligence",
    "calendar_harvester": "intelligence",
    "price_engine": "intelligence",

    # news
    "news_engine": "news", "news_classifier": "news",
    "news_models": "news", "news_taxonomy": "news",
    "news_normalizer": "news",
    "news_deduplicator": "news",
    "news_evidence_builder": "news",
    "market_story_builder": "news",
    "market_story_engine": "news",
    "market_catalyst": "news",
    "market_catalyst_engine": "news",
    "catalyst_mapper": "news",
    "catalyst_processor": "news",
    "impact_engine": "news", "impact_rules": "news",
    "symbol_matcher": "news",
    "auto_alias_builder": "news",

    # trading
    "execution": "trading",
    "paper_execution": "trading",
    "live_execution": "trading",
    "execution_quality": "trading",
    "execution_strategy_selector": "trading",
    "dhan_client": "trading", "broker_sync": "trading",
    "risk_manager": "trading",
    "risk_governor": "trading",
    "capital_manager": "trading",
    "capital_allocation_engine": "trading",
    "allocation_trigger_engine": "trading",
    "position_manager": "trading",
    "position_monitor": "trading",
    "position_intelligence": "trading",
    "position_recovery": "trading",
    "open_position_manager": "trading",
    "portfolio_ledger": "trading",
    "portfolio_risk_manager": "trading",
    "portfolio_intelligence_engine": "trading",
    "trade_selection_engine": "trading",
    "trade_controller": "trading",
    "trade_policy_manager": "trading",
    "trade_logger": "trading",
    "trade_analytics": "trading",
    "trade_forensics_v2": "trading",
    "dynamic_trade_manager": "trading",
    "charges_calculator": "trading",
    "edge_analyzer": "trading",
    "greeks_check": "trading",

    # notifications
    "telegram_notifier": "notifications",
    "telegram_command_center": "notifications",
    "telegram_daily_report": "notifications",
    "event_logger": "notifications",
    "error_logger": "notifications",

    # repositories
    "database": "repositories",
}

DOCS = [
    "ARCHITECTURE_HANDBOOK_v1.0.xlsx",
    "CONVICTION_SPECIFICATION.md",
    "INSTITUTIONAL_TRADING_CONSTITUTION.md",
    "INSTITUTIONAL_TRADING_PLAYBOOK.md",
    "INTELLIGENCE_SNAPSHOT_SPEC.md",
    "MODULE_DEPENDENCIES.md",
    "NEWS_INTELLIGENCE_ARCHITECTURE_v1.0.md",
    "PROJECT_BRAIN.md",
    "PROJECT_BRAIN_V2.md",
    "SYSTEM_ARCHITECTURE.md",
]

ROOT_TESTS = [
    "test_breakout_filter.py", "test_bse.py",
    "test_bse_collector.py", "test_bse_corporate.py",
    "test_nse.py", "test_capital_allocation_engine.py",
    "test_opportunity_pool.py",
    "test_portfolio_replacement.py",
    "test_postgres.py", "test_railway_news_engine.py",
    "test_allocation_trigger_engine.py",
]

DELETE = [
    "brain_v2.py", "symbol_normalizer_v1.py",
    "check_master.py", "brain_repository.py",
    "error_log.txt", "gcm-diagnose.log",
    "project_files.txt", "trade_log_old.csv",
    "collectors/bse_collector.py",
    "collectors/commodity_collector.py",
    "collectors/global_collector.py",
    "collectors/government_collector.py",
    "collectors/moneycontrol_collector.py",
    "collectors/reuters_collector.py",
    "builders/build_orb.py",
    "builders/nse_orb_universe_builder.py",
    "repositories/experience_repository.py",
    "repositories/observation_repository.py",
    "repositories/trade_outcome_repository.py",
]

SKIP_DIRS = {".git", "__pycache__", ".agents", ".vscode"}

SHIM = (
    "import os\nimport sys\n\n"
    "sys.path.insert(0, os.path.dirname(os.path.dirname("
    "os.path.abspath(__file__))))\n\n"
)


def all_py_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS
        ]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def rewrite_imports(path, modules_desc):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    original = text

    for module in modules_desc:
        pkg = MAPPING[module]

        text = re.sub(
            rf"\bfrom {module} import",
            f"from {pkg}.{module} import",
            text,
        )
        text = re.sub(
            rf"^(\s*)import {module} as",
            rf"\1import {pkg}.{module} as",
            text,
            flags=re.M,
        )
        text = re.sub(
            rf"^(\s*)import {module}$",
            rf"\1from {pkg} import {module}",
            text,
            flags=re.M,
        )

    if text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    return False


def main():
    # 1. Deletions
    for rel in DELETE:
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            os.remove(path)
            print(f"deleted  {rel}")

    # 2. Create packages
    packages = sorted(set(MAPPING.values()))
    for pkg in packages:
        os.makedirs(os.path.join(ROOT, pkg), exist_ok=True)
        init = os.path.join(ROOT, pkg, "__init__.py")
        if not os.path.exists(init):
            with open(init, "w", encoding="utf-8") as f:
                f.write("")

    # 3. Move modules
    moved = 0
    for module, pkg in MAPPING.items():
        src = os.path.join(ROOT, f"{module}.py")
        dst = os.path.join(ROOT, pkg, f"{module}.py")
        if os.path.exists(src):
            shutil.move(src, dst)
            moved += 1
    print(f"moved    {moved} modules into packages")

    # 4. Rewrite imports everywhere
    modules_desc = sorted(
        MAPPING.keys(), key=len, reverse=True
    )
    changed = 0
    for path in all_py_files():
        if rewrite_imports(path, modules_desc):
            changed += 1
    print(f"rewrote  imports in {changed} files")

    # 5. Move docs
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    for doc in DOCS:
        src = os.path.join(ROOT, doc)
        if os.path.exists(src):
            shutil.move(
                src, os.path.join(ROOT, "docs", doc)
            )
    print("moved    docs → docs/")

    # 6. Move root tests into tests/ with path shim
    for name in ROOT_TESTS:
        src = os.path.join(ROOT, name)
        if not os.path.exists(src):
            continue
        with open(src, encoding="utf-8") as f:
            body = f.read()
        if "sys.path.insert" not in body:
            body = SHIM + body
        dst = os.path.join(ROOT, "tests", name)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(body)
        os.remove(src)
    print("moved    root tests → tests/")

    print("\nDONE — run verification next.")


if __name__ == "__main__":
    main()
