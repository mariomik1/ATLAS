from __future__ import annotations

from statistics import mean

from atlas_core.models import CatalystContext, CatalystEvent, DataQuality, FactorScore, NewsItem
from atlas_core.utils.indicators import clamp


class CatalystEngine:
    """Aggregates symbol-level news into a catalyst score and explanation.

    Sprint 3 is deliberately deterministic. It does not call an LLM and does not
    infer facts that are not present in NewsItem source data.
    """

    def __init__(self, settings: dict | None = None):
        cfg = (settings or {}).get("catalyst_engine", {})
        self.positive_threshold = float(cfg.get("positive_sentiment_threshold", 0.20))
        self.negative_threshold = float(cfg.get("negative_sentiment_threshold", -0.20))
        self.high_impact_threshold = float(cfg.get("high_impact_threshold", 75))

    def build(self, symbol: str, news: list[NewsItem], events: list[CatalystEvent] | None = None) -> CatalystContext:
        events = events or []
        symbol = symbol.upper()
        if not news:
            return CatalystContext(
                symbol=symbol,
                score=45,
                news_count=0,
                catalyst_type="none",
                upcoming_events=events,
                reasons=["No recent catalyst/news item is available in the configured provider."],
                risks=["Catalyst layer is incomplete; do not rely on AI narrative for this asset."],
                data_quality=DataQuality(provider="catalyst_engine", issues=["No news items for symbol."]),
            )

        sentiments = [item.sentiment_score for item in news]
        relevances = [item.relevance_score for item in news]
        impacts = [item.impact_score for item in news]
        avg_sentiment = mean(sentiments)
        avg_relevance = mean(relevances)
        avg_impact = mean(impacts)
        positive_count = sum(1 for item in news if item.sentiment_score >= self.positive_threshold)
        negative_count = sum(1 for item in news if item.sentiment_score <= self.negative_threshold)
        risk_count = sum(1 for item in news if item.risk_flag or item.risk_flags)
        event_types = sorted({item.event_type for item in news if item.event_type})
        top = sorted(news, key=lambda item: (item.relevance_score, item.impact_score), reverse=True)[:3]

        catalyst_type = "neutral"
        if positive_count and negative_count:
            catalyst_type = "mixed"
        elif positive_count:
            catalyst_type = "positive"
        elif negative_count:
            catalyst_type = "negative"

        score = 50.0
        score += avg_sentiment * 25.0
        score += (avg_relevance - 50.0) * 0.22
        score += (avg_impact - 50.0) * 0.18
        score += min(8, positive_count * 2.5)
        score -= min(12, negative_count * 3.5)
        score -= min(10, risk_count * 2.5)
        score = clamp(score)

        reasons = []
        risks = []
        primary = top[0].title if top else None
        if primary:
            reasons.append(f"Primary catalyst: {primary} ({top[0].source}).")
        if avg_sentiment >= self.positive_threshold:
            reasons.append(f"Average news sentiment is positive ({avg_sentiment:.2f}).")
        elif avg_sentiment <= self.negative_threshold:
            risks.append(f"Average news sentiment is negative ({avg_sentiment:.2f}).")
        else:
            reasons.append(f"Average news sentiment is neutral/mixed ({avg_sentiment:.2f}).")
        if avg_relevance >= 70:
            reasons.append(f"News relevance is high ({avg_relevance:.0f}/100).")
        if avg_impact >= self.high_impact_threshold:
            reasons.append(f"Catalyst impact is high ({avg_impact:.0f}/100).")
        if events:
            reasons.append(f"Upcoming/recent events tracked: {len(events)}.")
            if any(event.importance == "high" for event in events):
                score = min(100, score + 2)
                reasons.append("At least one high-importance event is in the catalyst calendar.")
        for item in top:
            if item.risk_flag or item.risk_flags:
                risks.append(f"Risk headline: {item.title} ({item.event_type}).")
        if not risks and risk_count == 0:
            risks.append("No explicit Sprint 3 news risk flag found; still validate with live sources before action.")

        quality = self._merge_quality(news)
        return CatalystContext(
            symbol=symbol,
            score=round(score, 2),
            news_count=len(news),
            average_sentiment=round(avg_sentiment, 3),
            average_relevance=round(avg_relevance, 2),
            average_impact=round(avg_impact, 2),
            primary_catalyst=primary,
            catalyst_type=catalyst_type,
            event_types=event_types,
            upcoming_events=events,
            news=top,
            positive_count=positive_count,
            negative_count=negative_count,
            risk_flag_count=risk_count,
            reasons=reasons[:5],
            risks=risks[:5],
            data_quality=quality,
        )

    def evaluate(self, context: CatalystContext, weight: float) -> FactorScore:
        return FactorScore(
            name="catalyst_ai",
            score=context.score,
            weight=weight,
            reasons=context.reasons or ["Catalyst context is neutral."],
            risks=context.risks,
            data_quality=context.data_quality,
        )

    @staticmethod
    def _merge_quality(news: list[NewsItem]) -> DataQuality:
        provider_names = sorted({item.data_quality.provider for item in news})
        issues = []
        for item in news:
            issues.extend(item.data_quality.issues)
        first = news[0].data_quality
        return DataQuality(
            level=first.level,
            provider="+".join(provider_names) if provider_names else "catalyst_engine",
            issues=sorted(set(issues)) or ["Catalyst data available."],
        )
