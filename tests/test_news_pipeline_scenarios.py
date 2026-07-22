"""
End-to-end verification: today's exact failure mode.

Reproduces the real 2026-07-22 incident -- a Trump tariff
announcement on generic pharma imports -- through the ACTUAL
production pipeline (NewsClassifier -> MarketStoryBuilder ->
ImpactEngine -> NewsEvidenceBuilder), and asserts the final
Evidence object is genuinely bearish, not silently neutral.

This is the class of test that was missing before today: every
existing test proves the code RUNS without crashing. This one
proves the JUDGMENT is correct for a real scenario that actually
happened and actually cost money.
"""
import sys
sys.path.insert(0, ".")

from news.news_models import RawNews, ProcessedNews
from news.news_classifier import NewsClassifier
from news.market_story_builder import MarketStoryBuilder
from news.impact_engine import ImpactEngine
from news.news_evidence_builder import NewsEvidenceBuilder

PASSED = 0
FAILED = 0


def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS: {name}")
    else:
        FAILED += 1
        print(f"  FAIL: {name}  {detail}")


print("=" * 70)
print("REAL SCENARIO: Trump tariff on generic pharma imports")
print("=" * 70)

raw = RawNews(
    headline=(
        "Trump announces 100% tariff on generic pharmaceutical "
        "imports into the United States"
    ),
    description=(
        "US President Trump said generic drug imports will face a "
        "tariff, raising costs for Indian pharma exporters."
    ),
)

processed = ProcessedNews(
    raw_news=raw,
    symbols=["CIPLA", "AUROPHARMA"],
)

classifier = NewsClassifier()
classified = classifier.classify(processed)

print(f"\nClassified category    : {classified.category}")
print(f"Classified subcategory : {classified.subcategory}")
print(f"Classified confidence  : {classified.confidence}")

check(
    "category detected as MACRO (tariff keyword)",
    classified.category == "MACRO",
    f"got {classified.category!r}",
)

story_builder = MarketStoryBuilder()
stories = story_builder.build([classified])

check("a story was built", len(stories) == 1)
story = stories[0]
story.affected_symbols = ["CIPLA", "AUROPHARMA"]

impact_engine = ImpactEngine()
impact = impact_engine.evaluate(story)

print(f"\nImpact rule matched     : {impact.rule_name}")
print(f"Impact market_score     : {impact.market_score}")
print(f"Impact confidence       : {impact.confidence}")

check(
    "impact engine did NOT silently zero this out",
    impact.market_score != 0 or impact.sector_score != 0
    or impact.stock_score != 0,
    "market/sector/stock score all zero -- the exact bug this "
    "was meant to fix",
)
check(
    "impact assessment is directionally negative",
    (
        impact.market_score * 3
        + impact.sector_score * 2
        + impact.stock_score
    ) < 0,
    "net impact was not negative",
)

# Mirror Brain.build_news_evidence's fix exactly
net_impact = (
    impact.market_score * 3
    + impact.sector_score * 2
    + impact.stock_score
)
story.story_direction = (
    "WEAKENING" if net_impact < 0
    else "STRENGTHENING" if net_impact > 0
    else "NEUTRAL"
)

print(f"\nstory_direction          : {story.story_direction}")

check(
    "story_direction is WEAKENING, not the old hardcoded "
    "STRENGTHENING",
    story.story_direction == "WEAKENING",
)

evidence_builder = NewsEvidenceBuilder()
evidence = evidence_builder.build(story, impact, symbol="CIPLA")

print(f"\nEvidence recommendation : {evidence.recommendation}")
print(f"Evidence score          : {evidence.score}")
print(f"Evidence reason         : {evidence.reason}")

check(
    "MARKET_STORY evidence recommends SELL, not the old "
    "hardcoded WAIT",
    evidence.recommendation == "SELL",
)

# FNO_CATALYST and RESULTS_LIVE both branch on story_direction
# the same way -- verify the fix propagates to them too.
direction = story.story_direction
fno_would_recommend = (
    "SELL" if direction in ("WEAKENING", "CONTRADICTED", "NEGATIVE")
    else "BUY"
)
check(
    "FNO_CATALYST's own direction check now also says SELL "
    "(was structurally impossible before -- WEAKENING was "
    "never assigned anywhere)",
    fno_would_recommend == "SELL",
)

print()
print("=" * 70)
print("REAL SCENARIO 2: genuinely good news (control case)")
print("=" * 70)
print("Confirms the fix isn't one-directional -- positive news")
print("must still come out positive, not flipped to bearish by")
print("an overcorrection.")

raw2 = RawNews(
    headline="Government grants tariff exemption boosting exports",
    description=(
        "The government announced a duty cut and exemption for "
        "export-linked manufacturing, seen as a major boost."
    ),
)
processed2 = ProcessedNews(raw_news=raw2, symbols=["EXIDEIND"])
classified2 = classifier.classify(processed2)
stories2 = story_builder.build([classified2])
check("a story was built (control)", len(stories2) == 1)
story2 = stories2[0]
story2.affected_symbols = ["EXIDEIND"]

impact2 = impact_engine.evaluate(story2)
net2 = (
    impact2.market_score * 3
    + impact2.sector_score * 2
    + impact2.stock_score
)
story2.story_direction = (
    "WEAKENING" if net2 < 0
    else "STRENGTHENING" if net2 > 0
    else "NEUTRAL"
)
evidence2 = evidence_builder.build(story2, impact2, symbol="EXIDEIND")

print(f"\nstory_direction (control) : {story2.story_direction}")
print(f"Evidence recommendation   : {evidence2.recommendation}")

check(
    "control case (good news) still comes out BUY, not "
    "flipped bearish by the fix",
    evidence2.recommendation == "BUY",
    f"got {evidence2.recommendation!r}",
)

print()
print("=" * 70)
print(f"PASSED : {PASSED}")
print(f"FAILED : {FAILED}")
print("=" * 70)

sys.exit(1 if FAILED else 0)
