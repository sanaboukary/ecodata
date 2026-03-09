#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visualisation de la structure du pipeline ETL"""

import sys
import io

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*120)
print(" " * 35 + "STRUCTURE DU PIPELINE ETL")
print("="*120)

print("""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        SOURCES DE DONNEES                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │     BRVM     │    │ World Bank   │    │     IMF      │    │     AfDB     │    │   UN SDG     │
    │   (Bourse)   │    │  (Économie)  │    │ (Monétaire)  │    │(Development) │    │    (ODD)     │
    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
           │                   │                   │                   │                   │
           │                   │                   │                   │                   │
           └───────────────────┴───────────────────┴───────────────────┴───────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CONNECTEURS (scripts/connectors/)                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  brvm_scraper_production.py     ──►  Scraping temps réel BRVM (BeautifulSoup + Selenium)           │
│  brvm.py                        ──►  API REST BRVM (si disponible)                                  │
│  brvm_publications.py           ──►  Documents PDF (rapports, communiqués)                          │
│                                                                                                      │
│  worldbank.py                   ──►  API World Bank (35+ indicateurs économiques)                   │
│  imf.py                         ──►  API IMF SDMX (20+ séries monétaires)                           │
│  afdb.py                        ──►  API AfDB SDMX (développement africain)                          │
│  un_sdg.py                      ──►  API UN (Objectifs de Développement Durable)                    │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  PIPELINE PRINCIPAL (scripts/pipeline.py)                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  run_ingestion(source, **kwargs)                                                                    │
│    │                                                                                                 │
│    ├──► 1. EXTRACTION:  fetch_xxx() depuis connecteur approprié                                     │
│    │                    Retourne: List[Dict] (records bruts)                                        │
│    │                                                                                                 │
│    ├──► 2. SAUVEGARDE RAW:  write_raw(db, source, records)                                          │
│    │                         Collection: raw_events (audit trail)                                   │
│    │                                                                                                 │
│    ├──► 3. NORMALISATION:  normalize_xxx(records)                                                   │
│    │                        Transforme vers schéma unifié:                                           │
│    │                        {source, dataset, key, ts, value, attrs}                                │
│    │                                                                                                 │
│    ├──► 4. SAUVEGARDE CURATED:  upsert_observations(db, observations)                               │
│    │                             Collection: curated_observations                                   │
│    │                                                                                                 │
│    └──► 5. LOG EXECUTION:  log_ingestion_run(db, source, status, duration, obs_count)              │
│                            Collection: ingestion_runs                                               │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    NORMALISATION PAR SOURCE                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  normalize_brvm(records)        ──► {source: "BRVM", dataset: "QUOTES", key: symbol,                │
│                                      value: close, attrs: {open, high, low, volume,                 │
│                                      market_cap, pe_ratio, dividend_yield, rsi, ...}}               │
│                                                                                                      │
│  normalize_worldbank(records)   ──► {source: "WorldBank", dataset: indicator_code,                  │
│                                      key: country_code, value: numeric_value,                       │
│                                      attrs: {indicator_name, unit, ...}}                            │
│                                                                                                      │
│  normalize_imf(records)         ──► {source: "IMF", dataset: series_code,                           │
│                                      key: area_code, value: numeric_value,                          │
│                                      attrs: {series_name, freq, unit, ...}}                         │
│                                                                                                      │
│  normalize_afdb(records)        ──► {source: "AfDB", dataset: indicator_code,                       │
│                                      key: country_code, value: numeric_value}                       │
│                                                                                                      │
│  normalize_un_sdg(records)      ──► {source: "UN_SDG", dataset: goal_target,                        │
│                                      key: country_code, value: numeric_value}                       │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    MONGODB (centralisation_db)                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐          │
│  │   raw_events             │  │  curated_observations    │  │   ingestion_runs         │          │
│  │   (Audit Trail)          │  │  (Données Normalisées)   │  │   (Logs Execution)       │          │
│  ├──────────────────────────┤  ├──────────────────────────┤  ├──────────────────────────┤          │
│  │ - Réponses API brutes    │  │ - source                 │  │ - source                 │          │
│  │ - Immuables              │  │ - dataset                │  │ - status                 │          │
│  │ - Timestamp ingestion    │  │ - key                    │  │ - start_time             │          │
│  │ - Source                 │  │ - ts                     │  │ - end_time               │          │
│  │                          │  │ - value                  │  │ - duration_sec           │          │
│  │                          │  │ - attrs {}               │  │ - obs_count              │          │
│  │                          │  │                          │  │ - error_msg              │          │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘          │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ORCHESTRATION & SCHEDULING                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  AIRFLOW (Production)                           DJANGO COMMANDS (Manuel)                            │
│  ├─ worldbank_dag.py (mensuel, 15 à 2h00)      ├─ python manage.py ingest_source --source brvm     │
│  ├─ imf_dag.py (mensuel, 1er à 2h30)           ├─ python manage.py ingest_source --source worldbank│
│  ├─ afdb_un_dag.py (trimestriel)               ├─ python manage.py ingest_source --source imf      │
│  ├─ brvm_complete_daily.py (quotidien 17h)     └─ python manage.py ingest_source --source afdb     │
│  └─ master_complete_dag.py (hebdomadaire)                                                           │
│                                                                                                      │
│  REST API (Programmatique)                                                                          │
│  └─ POST /api/ingestion/start/ {source: "brvm"}                                                     │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    UTILISATION DES DONNEES                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  DASHBOARD (dashboard/views.py)                 ANALYSE IA (analyse_ia_simple.py)                   │
│  ├─ Visualisation temps réel                    ├─ Indicateurs techniques (RSI, MACD, SMA)         │
│  ├─ Graphiques interactifs                      ├─ Prédictions 7 jours                             │
│  ├─ Tableaux de bord sectoriels                 ├─ Recommandations BUY/HOLD/SELL                   │
│  └─ Alertes & notifications                     └─ Scoring de confiance                            │
│                                                                                                      │
│  CORRELATION ENGINE                             BACKTEST SERVICE                                    │
│  ├─ BRVM ↔ PIB/Inflation                        ├─ Simulation stratégies                           │
│  ├─ Actions ↔ Secteurs                          ├─ Performance historique                          │
│  └─ Macro ↔ Micro                               └─ Métriques de risque                             │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "="*120)
print("SCHEMA UNIFIE - curated_observations")
print("="*120)

print("""
{
  "source": "BRVM" | "WorldBank" | "IMF" | "AfDB" | "UN_SDG" | "AI_ANALYSIS",
  "dataset": "QUOTES" | "SP.POP.TOTL" | "PCPI_IX" | ...,
  "key": "SNTS" | "CI" | "SN" | ...,
  "ts": "2025-12-08",
  "value": 15500.0,
  "attrs": {
    // Attributs spécifiques à la source
    // BRVM: open, high, low, volume, market_cap, pe_ratio, rsi, macd, recommendation, ...
    // WorldBank: indicator_name, unit, country_name, ...
    // IMF: series_name, frequency, unit, ...
    // AfDB: indicator_name, country_name, ...
    // UN_SDG: goal, target, indicator, ...
  }
}
""")

print("\n" + "="*120)
print("FLUX DE DONNEES - Exemple BRVM")
print("="*120)

print("""
1. EXTRACTION (brvm_scraper_production.py):
   └─► Scrape https://www.brvm.org/fr/cours-et-cotations
   └─► Retourne: [{"symbol": "SNTS", "close": 15500, "open": 15400, "volume": 1200, ...}]

2. SAUVEGARDE RAW (mongo_utils.write_raw):
   └─► INSERT raw_events: {"source": "BRVM", "data": [...], "ingested_at": "2026-01-06T12:00:00"}

3. NORMALISATION (pipeline.normalize_brvm):
   └─► Transforme: {"symbol": "SNTS", "close": 15500, ...}
   └─► En: {"source": "BRVM", "dataset": "QUOTES", "key": "SNTS", "ts": "2026-01-06", 
            "value": 15500, "attrs": {"open": 15400, "volume": 1200, ...}}

4. SAUVEGARDE CURATED (mongo_utils.upsert_observations):
   └─► UPSERT curated_observations (évite doublons via index unique)

5. LOG EXECUTION (mongo_utils.log_ingestion_run):
   └─► INSERT ingestion_runs: {"source": "BRVM", "status": "success", "obs_count": 47, ...}
""")

print("\n" + "="*120)
print("CONNECTEURS DISPONIBLES")
print("="*120)

print("""
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Source      │ Fichier                        │ Fonction                │ Fréquence    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ BRVM        │ brvm_scraper_production.py     │ scrape_brvm_data()      │ Temps réel   │
│ BRVM PDF    │ brvm_publications.py           │ fetch_brvm_publications │ Quotidien    │
│ World Bank  │ worldbank.py                   │ fetch_worldbank_indic() │ Mensuel      │
│ IMF         │ imf.py                         │ fetch_imf_compact()     │ Mensuel      │
│ AfDB        │ afdb.py                        │ fetch_afdb_sdmx()       │ Trimestriel  │
│ UN SDG      │ un_sdg.py                      │ fetch_un_sdg()          │ Annuel       │
└────────────────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "="*120)
print("POINTS D'ENTREE")
print("="*120)

print("""
1. MANUEL (Django Management Command):
   python manage.py ingest_source --source brvm
   python manage.py ingest_source --source worldbank --indicator SP.POP.TOTL --country CI

2. PROGRAMMATIQUE (REST API):
   POST http://localhost:8000/api/ingestion/start/
   Body: {"source": "brvm"}

3. AUTOMATIQUE (Airflow DAGs):
   Airflow Scheduler → DAG → Tâche → run_ingestion(source, **kwargs)

4. SCRIPT DIRECT (Python):
   from scripts.pipeline import run_ingestion
   obs_count = run_ingestion('brvm')
""")

print("\n" + "="*120)
print("VERIFICATION")
print("="*120)

print("""
# Voir les données collectées
python voir_donnees.py

# Historique d'ingestion
python show_ingestion_history.py

# Rapport complet
python show_complete_data.py

# Inspection approfondie
python inspection_approfondie.py
""")

print("="*120)
