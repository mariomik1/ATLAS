from __future__ import annotations

from atlas_core.config_loader import load_all_configs
from atlas_core.engines.ai_narrative_engine import AINarrativeEngine
from atlas_core.engines.catalyst_engine import CatalystEngine
from atlas_core.engines.chart_engine import ChartEngine
from atlas_core.engines.fire_engine import FireEngine
from atlas_core.engines.fundamental_engine import FundamentalEngine
from atlas_core.engines.journal_engine import JournalEngine
from atlas_core.engines.market_engine import MarketEngine
from atlas_core.engines.portfolio_engine import PortfolioEngine
from atlas_core.engines.risk_engine import RiskEngine
from atlas_core.engines.strategy_engine import StrategyEngine
from atlas_core.engines.trade_plan_engine import TradePlanEngine
from atlas_core.models import DailyBriefing, FactorScore, MarketSnapshot, Recommendation
from atlas_core.providers.identifier_resolver import IdentifierResolver
from atlas_core.providers.manual_provider import ManualSampleProvider
from atlas_core.providers.news_provider import CsvSampleNewsProvider
from atlas_core.providers.live_news_provider import MarketauxNewsProvider, NewsApiProvider
from atlas_core.providers.status import ProviderRegistry
from atlas_core.scoring.atlas_score import AtlasScoreEngine
from atlas_core.scoring.gates import verdict_from_score
from atlas_core.scoring.weights import weights_for_intent


class AtlasOrchestrator:
    def __init__(self, configs: dict | None = None):
        self.configs = configs or load_all_configs()
        self.settings = self.configs["settings"]
        self.scoring_config = self.configs["scoring_weights"]
        self.provider_registry = ProviderRegistry(self.settings)
        self.provider = ManualSampleProvider(self.configs["watchlists"], settings=self.settings)
        self.identifier_resolver = IdentifierResolver(self.provider)
        self.market_engine = MarketEngine(self.settings)
        self.fundamental_engine = FundamentalEngine()
        self.chart_engine = ChartEngine()
        self.news_provider = self._build_news_provider()
        self.catalyst_engine = CatalystEngine(self.settings)
        self.strategy_engine = StrategyEngine()
        self.trade_plan_engine = TradePlanEngine()
        self.risk_engine = RiskEngine(self.configs["risk_rules"])
        self.score_engine = AtlasScoreEngine()
        self.ai_engine = AINarrativeEngine()
        self.portfolio_engine = PortfolioEngine(self.configs["portfolio"])
        self.fire_engine = FireEngine(self.configs.get("portfolio", {}).get("fire", {}))
        self.journal_engine = JournalEngine()
        self._market_snapshot: MarketSnapshot | None = None


    def _live_enabled(self, cfg: dict) -> bool:
        return bool(cfg.get("live_providers_enabled", self.settings.get("provider_activation", {}).get("live_providers_enabled", False)))

    def _build_news_provider(self):
        from atlas_core.utils.env_loader import get_secret, load_env_file
        from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
        cfg = self.settings.get("news", {})
        provider_name = str(cfg.get("provider", "csv_sample")).lower()
        fallback = CsvSampleNewsProvider(self.settings)
        cache = JsonFileCache(self.settings.get("cache", {}).get("base_dir", "data/cache"))
        audit = FetchAuditLogger(self.settings.get("audit", {}).get("fetch_log_path", "data/cache/fetch_audit.jsonl"))
        ttl = int(float(cfg.get("cache_ttl_minutes", 120)) * 60)
        env_values = load_env_file()
        common = dict(
            settings=self.settings,
            fallback_provider=fallback,
            cache=cache,
            audit=audit,
            ttl_seconds=ttl,
            live_enabled=self._live_enabled(cfg),
            stale_allowed=bool(self.settings.get("cache", {}).get("stale_allowed_when_provider_fails", True)),
        )
        if provider_name == "marketaux":
            return MarketauxNewsProvider(api_key=get_secret("MARKETAUX_API_KEY", env_values), **common)
        if provider_name == "newsapi":
            return NewsApiProvider(api_key=get_secret("NEWSAPI_API_KEY", env_values), **common)
        # FMP news can be added later; FMP provider remains registered for readiness in Sprint 6B.
        return fallback

    def get_market_snapshot(self) -> MarketSnapshot:
        if self._market_snapshot is None:
            self._market_snapshot = self.market_engine.get_market_snapshot()
        return self._market_snapshot

    def build_recommendation_for_item(self, item, market: MarketSnapshot | None = None, portfolio=None) -> Recommendation:
        market = market or self.get_market_snapshot()
        portfolio = portfolio or self.portfolio_engine.snapshot()
        chart_context = self.chart_engine.analyze(item)
        fundamental_context = self.fundamental_engine.context_for(item)
        news_items = self.news_provider.get_news_for_symbol(item.asset.symbol)
        catalyst_events = self.news_provider.get_events_for_symbol(item.asset.symbol)
        catalyst_context = self.catalyst_engine.build(item.asset.symbol, news_items, catalyst_events)
        intent, strategy = self.strategy_engine.assign(item, chart_context=chart_context)
        weights = weights_for_intent(self.scoring_config, intent.value)
        trade_plan = self.trade_plan_engine.build(item, strategy, chart_context=chart_context)
        portfolio_fit = self.risk_engine.portfolio_fit(item, market, trade_plan, portfolio=portfolio)
        factors = [
            FactorScore(
                name="market",
                score=market.score,
                weight=weights.get("market", 0),
                reasons=[market.summary],
                risks=market.warnings[:2],
                data_quality=market.data_quality,
            ),
            self.fundamental_engine.evaluate(item, weights.get("fundamentals", 0)),
            self.chart_engine.evaluate_momentum(item, weights.get("momentum", 0)),
            self.chart_engine.evaluate_timing(item, weights.get("chart_timing", 0)),
            self.risk_engine.evaluate(item, weights.get("risk", 0)),
            FactorScore(
                name="portfolio_fit",
                score=portfolio_fit.score,
                weight=weights.get("portfolio_fit", 0),
                reasons=portfolio_fit.advisory_notes,
                risks=portfolio_fit.warnings,
                data_quality=item.data_quality,
            ),
            self.catalyst_engine.evaluate(catalyst_context, weights.get("catalyst_ai", 0)),
        ]
        score_breakdown = self.score_engine.combine(factors)
        verdict = verdict_from_score(score_breakdown.total_score, portfolio_fit.score, market.regime)
        reasons, risks = [], []
        for factor in factors:
            reasons.extend(factor.reasons[:1])
            risks.extend(factor.risks[:1])
        if trade_plan.reward_risk_ratio < 1.2:
            risks.append("CRV is weak in proxy levels; do not execute without chart review.")
        ai_statement = self.ai_engine.statement_for_candidate(
            item.asset.symbol,
            verdict.value,
            score_breakdown.total_score,
            reasons,
            risks,
            catalyst_context=catalyst_context,
            fundamental_context=fundamental_context,
        )
        rec = Recommendation(
            asset=item.asset,
            intent=intent,
            verdict=verdict,
            strategy=strategy,
            atlas_score=score_breakdown.total_score,
            score_breakdown=score_breakdown,
            market_snapshot=market,
            portfolio_fit=portfolio_fit,
            trade_plan=trade_plan,
            chart_context=chart_context,
            catalyst_context=catalyst_context,
            fundamental_context=fundamental_context,
            key_reasons=reasons[:6],
            key_risks=risks[:6],
            ai_statement=ai_statement,
            data_quality=item.data_quality,
            back_book_summary={"status": "pending"},
        )
        rec.back_book_summary = self.journal_engine.back_book_record(rec)
        return rec

    def daily_briefing(self) -> DailyBriefing:
        market = self.get_market_snapshot()
        portfolio = self.portfolio_engine.snapshot()
        fire = self.fire_engine.build_snapshot(portfolio)
        market_catalysts = self.catalyst_engine.build("MARKET", self.news_provider.get_market_news(), [])
        recommendations = [
            self.build_recommendation_for_item(item, market=market, portfolio=portfolio)
            for item in self.provider.get_watchlist_market_data()
        ]
        recommendations.sort(key=lambda rec: (rec.atlas_score, rec.portfolio_fit.score), reverse=True)
        max_candidates = int(self.settings.get("market", {}).get("max_daily_candidates", 10))
        recommendations = recommendations[:max_candidates]
        has_trade = any(rec.atlas_score >= 82 for rec in recommendations)
        provider_summary = self.provider_registry.summary()
        headline = "Chancen und Vermögensentwicklung: Atlas Technical MVP briefing is ready."
        no_trade_message = None if has_trade else self.settings.get("market", {}).get("no_trade_message")
        actions = list(portfolio.advisory_actions or self.portfolio_engine.advisory_actions(portfolio))
        actions.append(
            f"Market catalysts: {market_catalysts.score:.0f}/100 from {market_catalysts.news_count} sample news item(s)."
        )
        actions.append(f"Market permission: {market.trade_permission}; position multiplier {market.position_size_multiplier:.2f}.")
        actions.append(
            f"Provider status: {provider_summary.ready}/{provider_summary.total} ready; "
            f"{provider_summary.missing_keys} missing API key(s); {provider_summary.disabled_live} disabled live provider(s)."
        )
        actions.append("Review entries, stops, take-profit levels, fundamentals and catalyst flags manually before any action.")
        executive_summary = [
            f"Market: {market.regime} ({market.score:.0f}/100), permission {market.trade_permission}.",
            f"FIRE: {fire.progress_pct:.1f}% funded; projected target year {fire.projected_year}.",
            f"Portfolio: EUR {portfolio.total_tracked_eur:,.0f} tracked, cash {portfolio.cash_pct:.1f}%.",
            f"Candidates: {len(recommendations)} shown; {'no high-conviction trade today' if no_trade_message else 'at least one candidate clears quality threshold'}.",
        ]
        data_quality_notes = sorted({issue for rec in recommendations for issue in rec.data_quality.issues[:2]})[:10]
        return DailyBriefing(
            market=market,
            portfolio=portfolio,
            fire=fire,
            market_catalysts=market_catalysts,
            headline=headline,
            no_trade_message=no_trade_message,
            recommendations=recommendations,
            actions=actions,
            executive_summary=executive_summary,
            data_quality_notes=data_quality_notes,
        )

    def append_daily_recommendations_to_journal(self) -> str:
        briefing = self.daily_briefing()
        path = self.journal_engine.append_recommendations(briefing.recommendations)
        return str(path)


    def _headline(self, market: MarketSnapshot, recommendations: list[Recommendation], portfolio, fire) -> str:
        trade_count = sum(1 for rec in recommendations if rec.atlas_score >= 82)
        best = recommendations[0].asset.symbol if recommendations else "none"
        return (
            f"Chancen und Vermögensentwicklung: {market.regime} market, "
            f"{trade_count} candidate(s) above action threshold, best setup {best}, "
            f"FIRE progress {fire.progress_pct:.1f}% with EUR {portfolio.total_tracked_eur:,.0f} tracked."
        )

    def analyze_query(self, query: str) -> Recommendation | None:
        item = self.identifier_resolver.resolve(query)
        if item is None:
            return None
        return self.build_recommendation_for_item(item)

    def search_assets(self, query: str, limit: int = 10):
        return self.identifier_resolver.search(query, limit=limit)
