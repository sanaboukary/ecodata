from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import random, os, requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .brvm_stocks import BRVM_STOCKS, get_all_symbols

BRVM_API_URL = os.getenv("BRVM_API_URL","").strip()
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT","30"))

class BRVMClientError(Exception): pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True,
       retry=retry_if_exception_type((requests.RequestException, BRVMClientError)))
def fetch_brvm(api_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère les données de toutes les actions cotées à la BRVM
    
    Args:
        api_url: URL de l'API BRVM (optionnel, utilise BRVM_API_URL si non fourni)
        
    Returns:
        Liste de dictionnaires avec les données de cotation de chaque action
    """
    url = (api_url or BRVM_API_URL).strip()
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    
    if not url:
        # Simulation avec toutes les vraies actions BRVM si pas d'API configurée
        symbols = get_all_symbols()
        out = []
        
        for symbol in symbols:
            stock_info = BRVM_STOCKS[symbol]
            
            # Générer des données de cotation réalistes
            # Prix de base selon le secteur
            base_price = {
                "Banque": random.uniform(4000, 8000),
                "Assurance": random.uniform(3000, 6000),
                "Industrie": random.uniform(1000, 5000),
                "Agriculture": random.uniform(500, 3000),
                "Distribution": random.uniform(1500, 4000),
                "Transport": random.uniform(2000, 5000),
                "Services Publics": random.uniform(1500, 4500),
                "Autres": random.uniform(1000, 4000)
            }.get(stock_info["sector"], 2000)
            
            # Variation intraday réaliste (-2% à +2%)
            variation = random.uniform(-0.02, 0.02)
            open_price = round(base_price, 2)
            close_price = round(base_price * (1 + variation), 2)
            high_price = round(max(open_price, close_price) * random.uniform(1.00, 1.01), 2)
            low_price = round(min(open_price, close_price) * random.uniform(0.99, 1.00), 2)
            
            # Volume selon la liquidité du titre
            volume = random.randint(100, 50_000)
            
            # === MÉTRIQUES AVANCÉES POUR INVESTISSEURS ===
            
            # 1. Performance & Volatilité
            day_change = close_price - open_price
            day_change_pct = round((day_change / open_price) * 100, 2)
            week_change_pct = round(random.uniform(-5, 5), 2)
            month_change_pct = round(random.uniform(-10, 15), 2)
            ytd_change_pct = round(random.uniform(-20, 30), 2)
            
            # 2. Valorisation & Ratios Financiers
            shares_outstanding = random.randint(1_000_000, 50_000_000)
            market_cap = close_price * shares_outstanding  # Capitalisation boursière
            
            # P/E Ratio (Price-to-Earnings) - secteur dépendant
            pe_ratio = round(random.uniform(8, 25) if stock_info["sector"] in ["Banque", "Assurance"] 
                           else random.uniform(10, 30), 2)
            
            # P/B Ratio (Price-to-Book)
            pb_ratio = round(random.uniform(0.8, 3.5), 2)
            
            # EPS (Earnings Per Share)
            eps = round(close_price / pe_ratio, 2)
            
            # 3. Dividendes
            dividend_yield = round(random.uniform(2, 8), 2)  # Rendement dividende (%)
            dividend_per_share = round((close_price * dividend_yield) / 100, 2)
            payout_ratio = round(random.uniform(30, 70), 2)  # Taux de distribution
            
            # 4. Liquidité & Volume
            avg_volume_30d = random.randint(5000, 100_000)
            turnover_rate = round((volume / shares_outstanding) * 100, 3)  # Taux de rotation
            
            # 5. Analyse Technique
            sma_20 = round(close_price * random.uniform(0.98, 1.02), 2)  # Moyenne mobile 20j
            sma_50 = round(close_price * random.uniform(0.95, 1.05), 2)  # Moyenne mobile 50j
            rsi = round(random.uniform(30, 70), 2)  # RSI (30-70 = neutre)
            beta = round(random.uniform(0.7, 1.3), 2)  # Volatilité vs marché
            
            # 6. Niveaux de Support/Résistance
            support_level = round(low_price * 0.98, 2)
            resistance_level = round(high_price * 1.02, 2)
            
            # 7. Santé Financière
            roe = round(random.uniform(5, 25), 2)  # Return on Equity (%)
            roa = round(random.uniform(2, 15), 2)  # Return on Assets (%)
            debt_to_equity = round(random.uniform(0.2, 1.5), 2)
            current_ratio = round(random.uniform(1.0, 2.5), 2)  # Liquidité
            
            # 8. Recommandations Analyste
            recommendations = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
            weights = [0.15, 0.30, 0.35, 0.15, 0.05]  # Probabilités
            recommendation = random.choices(recommendations, weights=weights)[0]
            
            # Score consensus (1-5, 5=Strong Buy)
            consensus_score = {
                "Strong Buy": 5, "Buy": 4, "Hold": 3, "Sell": 2, "Strong Sell": 1
            }[recommendation]
            
            target_price = round(close_price * random.uniform(0.9, 1.2), 2)
            price_to_target_pct = round(((target_price - close_price) / close_price) * 100, 2)
            
            # 9. Qualité du Titre
            # Score de liquidité (1-10)
            liquidity_score = min(10, int((volume / 5000) * 2))
            
            # Score de croissance (basé sur YTD)
            growth_score = min(10, max(1, int((ytd_change_pct + 20) / 5)))
            
            # Score de dividende
            dividend_score = min(10, int(dividend_yield))
            
            # 10. Informations Sectorielles
            sector_avg_pe = round(random.uniform(12, 20), 2)
            sector_performance = round(random.uniform(-5, 10), 2)
            
            out.append({
                "symbol": symbol,
                "ts": now.isoformat(),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "source": "BRVM",
                "name": stock_info["name"],
                "sector": stock_info["sector"],
                "country": stock_info["country"],
                
                # Métriques enrichies pour investisseurs
                "day_change": day_change,
                "day_change_pct": day_change_pct,
                "week_change_pct": week_change_pct,
                "month_change_pct": month_change_pct,
                "ytd_change_pct": ytd_change_pct,
                
                "market_cap": market_cap,
                "shares_outstanding": shares_outstanding,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "eps": eps,
                
                "dividend_yield": dividend_yield,
                "dividend_per_share": dividend_per_share,
                "payout_ratio": payout_ratio,
                
                "avg_volume_30d": avg_volume_30d,
                "turnover_rate": turnover_rate,
                
                "sma_20": sma_20,
                "sma_50": sma_50,
                "rsi": rsi,
                "beta": beta,
                
                "support_level": support_level,
                "resistance_level": resistance_level,
                
                "roe": roe,
                "roa": roa,
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
                
                "recommendation": recommendation,
                "consensus_score": consensus_score,
                "target_price": target_price,
                "price_to_target_pct": price_to_target_pct,
                
                "liquidity_score": liquidity_score,
                "growth_score": growth_score,
                "dividend_score": dividend_score,
                
                "sector_avg_pe": sector_avg_pe,
                "sector_performance": sector_performance
            })
        
        return out
    
    # Si une API est configurée, l'utiliser
    r = requests.get(url, timeout=HTTP_TIMEOUT)
    if r.status_code != 200:
        raise BRVMClientError(f"HTTP {r.status_code}")
    data = r.json()
    records = data.get("records") or data
    out=[]
    for rec in records:
        try:
            symbol = rec["symbol"]
            stock_info = BRVM_STOCKS.get(symbol, {})
            
            out.append({
                "symbol": symbol,
                "ts": rec.get("datetime") or rec.get("ts") or now.isoformat(),
                "open": float(rec["open"]), 
                "high": float(rec["high"]),
                "low": float(rec["low"]), 
                "close": float(rec["close"]),
                "volume": int(rec.get("volume") or 0), 
                "source": "BRVM",
                "name": stock_info.get("name", symbol),
                "sector": stock_info.get("sector", "Unknown"),
                "country": stock_info.get("country", "Unknown")
            })
        except Exception:
            continue
    return out
