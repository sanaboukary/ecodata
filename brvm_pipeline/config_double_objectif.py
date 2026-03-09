#!/usr/bin/env python3
"""
⚙️ CONFIGURATION DOUBLE OBJECTIF - TOP5 + OPPORTUNITY ENGINES

Ce fichier centralise TOUS les paramètres modifiables des deux moteurs :
- TOP5 Engine (performance publique hebdo)
- Opportunity Engine (détection précoce J+1 à J+7)

⚠️  PRINCIPE : Les deux moteurs ont des objectifs différents = paramètres différents
"""

# ============================================================================
# 🟢 TOP5 ENGINE - PERFORMANCE PUBLIQUE HEBDO
# ============================================================================

TOP5_CONFIG = {
    # OBJECTIF
    'objectif_principal': 'Être dans TOP5 hebdo officiel BRVM/RichBourse',
    'kpi': 'Taux de présence dans TOP5 officiel (target ≥60%)',
    
    # POIDS COMPOSANTES (doivent sommer à 1.0)
    'weights': {
        'expected_return': 0.30,        # Highest - potentiel gain
        'volume_acceleration': 0.25,    # Liquidité soudaine
        'semantic_score': 0.20,         # News/annonces
        'wos_setup': 0.15,              # Setup technique
        'risk_reward': 0.10             # Ratio RR
    },
    
    # SEUILS DÉCISION
    'thresholds': {
        'buy': 70,          # ≥ 70 = BUY
        'hold': 40,         # 40-70 = HOLD
        'sell': 40          # < 40 = SELL
    },
    
    # CALIBRATION BRVM (RSI, ATR, etc.)
    'brvm_calibration': {
        'rsi': {
            'period': 14,
            'oversold': 40,     # BRVM-specific (not 30)
            'overbought': 65    # BRVM-specific (not 70)
        },
        'atr_pct': {
            'period': 8,        # weeks
            'low': 8.0,         # % (BRVM normal range)
            'high': 25.0        # %
        },
        'sma': {
            'fast': 5,          # weeks (not days)
            'slow': 10          # weeks
        },
        'volume': {
            'period': 8         # weeks average
        },
        'volatility': {
            'period': 12        # weeks normalization
        }
    },
    
    # SÉLECTIVITÉ
    'max_selections': 5,        # Maximum 5 actions (TOP5)
    'min_history_weeks': 14,    # Minimum historique pour calcul
    
    # AUTO-LEARNING
    'learning': {
        'enabled': True,
        'learning_rate': 0.05,              # 5% ajustement
        'analysis_window_weeks': 12,        # 3 mois
        'min_samples': 8,                   # Min comparaisons
        'weight_constraints': {
            'min': 0.05,                    # Poids min 5%
            'max': 0.40                     # Poids max 40%
        }
    }
}

# ============================================================================
# 🔴 OPPORTUNITY ENGINE - DÉTECTION PRÉCOCE
# ============================================================================

OPPORTUNITY_CONFIG = {
    # OBJECTIF
    'objectif_principal': 'Détecter AVANT les autres (J+1 à J+7)',
    'kpi': 'Taux de conversion opportunité → mouvement significatif (target ≥40%)',
    
    # POIDS COMPOSANTES (doivent sommer à 1.0)
    'weights': {
        'volume_acceleration': 0.35,        # Highest - accumulation
        'semantic_impact': 0.30,            # News avant réaction
        'volatility_expansion': 0.20,       # Réveil
        'sector_momentum': 0.15             # Rattrapage
    },
    
    # SEUILS DÉTECTION
    'thresholds': {
        'strong_opportunity': 70,       # ≥ 70 = FORTE
        'weak_opportunity': 55,         # 55-70 = OBSERVATION
        'ignore': 55                    # < 55 = IGNORER
    },
    
    # DÉTECTEUR 1 : NEWS SILENCIEUSE
    'detector_news_silent': {
        'semantic_min': 0,              # News positive minimum
        'price_change_max': 2.0,        # Prix max +2%
        'volume_ratio_max': 1.0,        # Volume ≤ moyenne
        'enabled': True
    },
    
    # DÉTECTEUR 2 : VOLUME ANORMAL
    'detector_volume_accumulation': {
        'volume_factor': 2.0,           # Volume × 2 minimum
        'price_range_min': -1.0,        # Prix min -1%
        'price_range_max': 2.0,         # Prix max +2%
        'enabled': True
    },
    
    # DÉTECTEUR 3 : RUPTURE DE SOMMEIL
    'detector_volatility_awakening': {
        'atr_ratio_min': 1.8,           # ATR_7j / ATR_30j
        'volume_increase_min': 1.1,     # Volume +10% min
        'enabled': True
    },
    
    # DÉTECTEUR 4 : RETARD SECTEUR
    'detector_sector_lag': {
        'sector_threshold': 15.0,       # Secteur > +15%
        'action_lag_required': True,    # Action < secteur
        'volume_rising_required': True, # Volume monte
        'enabled': True
    },
    
    # SÉLECTIVITÉ
    'max_opportunities': 10,            # Max 10 alertes/jour
    'min_level': 'OBSERVATION',         # Niveau minimum à afficher
    
    # PÉRIODES ANALYSE
    'periods': {
        'volume_avg_days': 20,          # Moyenne volume
        'atr_short_days': 7,            # ATR court terme
        'atr_long_days': 30,            # ATR long terme
        'sector_perf_days': 5           # Performance secteur
    }
}

# ============================================================================
# 💰 ALLOCATION CAPITAL
# ============================================================================

CAPITAL_ALLOCATION = {
    # RÉPARTITION RECOMMANDÉE
    'top5_pct': 0.65,               # 60-70% sur TOP5
    'opportunities_pct': 0.25,      # 20-30% sur opportunités
    'cash_pct': 0.10,               # 10-20% cash sécurité
    
    # TAILLE POSITIONS
    'top5_position_size': {
        'min_pct': 0.12,            # 12% minimum (5 positions)
        'max_pct': 0.20,            # 20% maximum
        'default_pct': 0.13         # 13% par défaut (5 × 13% = 65%)
    },
    
    'opportunity_position_size': {
        'initial_pct': 0.06,        # 6% entrée initiale (25% position)
        'max_pct': 0.12,            # 12% maximum (50% position)
        'increment_pct': 0.06       # 6% par ajout
    },
    
    # STOPS
    'top5_stop_loss': {
        'initial': -0.08,           # -8% initial
        'trailing': True,
        'breakeven_trigger': 0.10   # Breakeven si +10%
    },
    
    'opportunity_stop_loss': {
        'initial': -0.12,           # -12% initial (plus large)
        'trailing': True,
        'breakeven_trigger': 0.15   # Breakeven si +15%
    },
    
    # TAKE PROFIT OPPORTUNITÉS
    'opportunity_take_profit': {
        'tp1': {'level': 0.15, 'exit_pct': 0.30},  # +15% → 30%
        'tp2': {'level': 0.25, 'exit_pct': 0.40},  # +25% → 40%
        'tp3': {'level': 0.40, 'exit_pct': 0.30}   # +40% → 30% (trail)
    }
}

# ============================================================================
# 📊 MÉTRIQUES SUCCÈS
# ============================================================================

SUCCESS_METRICS = {
    'top5_engine': {
        'kpi_principal': 'Taux présence TOP5 officiel',
        'target': 0.60,                 # 60% (3/5 actions)
        'excellent': 0.80,              # 80% (4/5 actions)
        'secondary': {
            'avg_rank': 3.0,            # Rank moyen ≤ 3
            'avg_performance': 0.20     # Performance moyenne ≥ 20%
        }
    },
    
    'opportunity_engine': {
        'kpi_principal': 'Taux conversion → mouvement',
        'target': 0.40,                 # 40% opportunités → trades gagnants
        'excellent': 0.60,              # 60%
        'secondary': {
            'avg_delay_days': 4.0,      # Délai moyen détection → TOP5
            'detection_early': 0.70     # 70% détectées 3-7j avant
        }
    },
    
    'combined': {
        'kpi_principal': 'Performance mensuelle',
        'target': 0.15,                 # 15% par mois
        'excellent': 0.25               # 25% par mois
    }
}

# ============================================================================
# 🎯 SECTEURS BRVM
# ============================================================================

BRVM_SECTORS = {
    'BANQUE': [
        'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 
        'BOAM', 'BOAN', 'BOAS', 'CABC', 'CBIBF', 'SGBC', 
        'SIBC', 'SLBC', 'SMBC'
    ],
    'INDUSTRIE': [
        'NEIC', 'PALC', 'PRSC', 'SAFC', 'SCRC', 'SICC', 
        'SMBC', 'SNTS', 'SOGC', 'SPHC', 'TTLC', 'TTLS', 
        'UNLC', 'UNXC'
    ],
    'DISTRIBUTION': [
        'CFAC', 'SDCC', 'SDSC', 'SHEC', 'SOGB', 'STAC', 'STBC'
    ],
    'TRANSPORT': [
        'BOAN', 'ETIT', 'ORGT', 'SEMC', 'SIVC'
    ],
    'SERVICES': [
        'CIEC', 'ECOC', 'FTSC', 'LNBB', 'NSBC', 'NTLC', 
        'ONTBF', 'ORAC'
    ]
}

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Valider cohérence configuration"""
    errors = []
    
    # Vérifier poids sument à 1.0
    top5_sum = sum(TOP5_CONFIG['weights'].values())
    if abs(top5_sum - 1.0) > 0.001:
        errors.append(f"TOP5 weights sum = {top5_sum:.3f} (should be 1.0)")
    
    opp_sum = sum(OPPORTUNITY_CONFIG['weights'].values())
    if abs(opp_sum - 1.0) > 0.001:
        errors.append(f"OPPORTUNITY weights sum = {opp_sum:.3f} (should be 1.0)")
    
    # Vérifier allocation capital
    capital_sum = (
        CAPITAL_ALLOCATION['top5_pct'] +
        CAPITAL_ALLOCATION['opportunities_pct'] +
        CAPITAL_ALLOCATION['cash_pct']
    )
    if abs(capital_sum - 1.0) > 0.001:
        errors.append(f"Capital allocation sum = {capital_sum:.3f} (should be 1.0)")
    
    if errors:
        print("\n❌ ERREURS CONFIGURATION :")
        for error in errors:
            print(f"   • {error}")
        return False
    
    print("\n✅ Configuration validée")
    return True

# ============================================================================
# EXPORT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("⚙️  CONFIGURATION DOUBLE OBJECTIF BRVM")
    print("="*80 + "\n")
    
    print("🟢 TOP5 ENGINE")
    print(f"   Objectif : {TOP5_CONFIG['objectif_principal']}")
    print(f"   KPI      : {TOP5_CONFIG['kpi']}")
    print(f"   Poids    : {TOP5_CONFIG['weights']}")
    print()
    
    print("🔴 OPPORTUNITY ENGINE")
    print(f"   Objectif : {OPPORTUNITY_CONFIG['objectif_principal']}")
    print(f"   KPI      : {OPPORTUNITY_CONFIG['kpi']}")
    print(f"   Poids    : {OPPORTUNITY_CONFIG['weights']}")
    print()
    
    print("💰 ALLOCATION CAPITAL")
    print(f"   TOP5         : {CAPITAL_ALLOCATION['top5_pct']*100:.0f}%")
    print(f"   Opportunités : {CAPITAL_ALLOCATION['opportunities_pct']*100:.0f}%")
    print(f"   Cash         : {CAPITAL_ALLOCATION['cash_pct']*100:.0f}%")
    print()
    
    validate_config()
    
    print("\n" + "="*80 + "\n")
