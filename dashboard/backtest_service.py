"""
Service de backtesting pour stratégies de trading BRVM
"""
from datetime import datetime
from plateforme_centralisation.mongo import get_mongo_db
from collections import namedtuple

# Structure pour les résultats de backtest
BacktestResult = namedtuple('BacktestResult', [
    'pnl', 'win_rate', 'nb_trades', 'max_drawdown', 'trades'
])


def run_backtest(symbol, signal_func, start_date=None, end_date=None, initial_cash=100000):
    """
    Exécute un backtest sur une action BRVM.
    
    Args:
        symbol: Symbole de l'action (ex: 'BICC')
        signal_func: Fonction qui prend une observation et retourne 'buy', 'sell', ou 'hold'
        start_date: Date de début (format YYYY-MM-DD) ou None pour tout l'historique
        end_date: Date de fin (format YYYY-MM-DD) ou None pour aujourd'hui
        initial_cash: Capital initial en FCFA
    
    Returns:
        BacktestResult ou None si pas de données
    """
    _, db = get_mongo_db()
    
    # Construire la requête
    query = {'source': 'BRVM', 'key': symbol}
    
    if start_date:
        query['ts'] = {'$gte': start_date}
    if end_date:
        if 'ts' in query:
            query['ts']['$lte'] = end_date
        else:
            query['ts'] = {'$lte': end_date}
    
    # Récupérer les données historiques
    observations = list(db.curated_observations.find(query).sort('ts', 1))
    
    if not observations:
        return None
    
    # Initialisation
    cash = initial_cash
    position = 0  # Nombre d'actions détenues
    trades = []
    portfolio_values = []
    
    # Simulation du trading
    for i, obs in enumerate(observations):
        price = obs.get('value', 0)
        if price <= 0:
            continue
        
        # Calculer la valeur du portefeuille
        portfolio_value = cash + (position * price)
        portfolio_values.append(portfolio_value)
        
        # Obtenir le signal
        signal = signal_func(obs)
        
        # Exécuter le trade selon le signal
        if signal == 'buy' and cash >= price:
            # Acheter autant d'actions que possible
            shares_to_buy = int(cash / price)
            if shares_to_buy > 0:
                cost = shares_to_buy * price
                position += shares_to_buy
                cash -= cost
                trades.append({
                    'date': obs.get('ts'),
                    'action': 'BUY',
                    'price': price,
                    'shares': shares_to_buy,
                    'value': cost
                })
        
        elif signal == 'sell' and position > 0:
            # Vendre toutes les actions
            revenue = position * price
            cash += revenue
            trades.append({
                'date': obs.get('ts'),
                'action': 'SELL',
                'price': price,
                'shares': position,
                'value': revenue
            })
            position = 0
    
    # Calcul du P&L final
    final_value = cash + (position * observations[-1].get('value', 0))
    pnl = final_value - initial_cash
    pnl_pct = (pnl / initial_cash) * 100
    
    # Calcul du win rate
    winning_trades = 0
    for i in range(1, len(trades)):
        if trades[i]['action'] == 'SELL' and i > 0:
            buy_price = trades[i-1]['price']
            sell_price = trades[i]['price']
            if sell_price > buy_price:
                winning_trades += 1
    
    sell_trades = len([t for t in trades if t['action'] == 'SELL'])
    win_rate = (winning_trades / sell_trades * 100) if sell_trades > 0 else 0
    
    # Calcul du max drawdown
    max_drawdown = 0
    peak = portfolio_values[0] if portfolio_values else initial_cash
    for value in portfolio_values:
        if value > peak:
            peak = value
        drawdown = ((peak - value) / peak) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return BacktestResult(
        pnl=round(pnl, 2),
        win_rate=round(win_rate, 2),
        nb_trades=len(trades),
        max_drawdown=round(max_drawdown, 2),
        trades=trades
    )
