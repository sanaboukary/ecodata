@echo off
color 0A
cls
echo.
echo ================================================================================
echo.
echo                  SYSTEME DE PUBLICATIONS BRVM - PRET !
echo.
echo ================================================================================
echo.
echo  8 FICHIERS CREES :
echo.
echo  1. collecter_publications_brvm_intelligent.py  (21 KB - Collecteur)
echo  2. analyser_sentiment_publications.py          (14 KB - Analyseur)
echo  3. COLLECTER_PUBLICATIONS_BRVM.cmd             (Interface collecte)
echo  4. ANALYSER_SENTIMENT.cmd                      (Interface analyse)
echo  5. MENU_PUBLICATIONS.cmd                       (Menu principal)
echo  6. brvm_publications_quotidien.py              (DAG Airflow)
echo  7. GUIDE_PUBLICATIONS_SENTIMENT.md             (11 KB - Doc complete)
echo  8. test_publications_system.py                 (Tests)
echo.
echo ================================================================================
echo.
echo  FONCTIONNALITES :
echo.
echo  - Collecte 7 categories BRVM (Bulletins, Communiques, Rapports, etc.)
echo  - Scraping intelligent (PDF + HTML + Tableaux)
echo  - Analyse sentiment (positif/negatif/neutre)
echo  - Detection evenements financiers (resultats, dividendes, AG)
echo  - Generation signaux trading (BUY/HOLD/SELL)
echo  - Score -1.0 a +1.0 pour chaque emetteur
echo  - Dashboard web : http://127.0.0.1:8000/brvm/publications/
echo  - API REST + Export CSV/JSON
echo  - Automatisation Airflow (18h quotidien)
echo.
echo ================================================================================
echo.
echo  DEMARRAGE RAPIDE (3 ETAPES) :
echo.
echo  1. Double-cliquez : COLLECTER_PUBLICATIONS_BRVM.cmd
echo     ^> Option 1 (Collecte COMPLETE)
echo     ^> Duree : 5-10 minutes
echo     ^> Resultat : 100-300 publications
echo.
echo  2. Double-cliquez : ANALYSER_SENTIMENT.cmd
echo     ^> Option 1 (30 jours)
echo     ^> Duree : 1-2 minutes
echo     ^> Resultat : Sentiment calcule
echo.
echo  3. Ouvrir navigateur : http://127.0.0.1:8000/brvm/publications/
echo     ^> Voir publications avec sentiment
echo     ^> Filtrer par categorie/emetteur
echo     ^> Exporter donnees
echo.
echo ================================================================================
echo.
echo  EXEMPLE SIGNAL TRADING :
echo.
echo  Emetteur : SNTS (Sonatel)
echo  Publications : 15
echo  Sentiment moyen : 0.65 (positif)
echo  Signal : BUY
echo  Breakdown : 12 positives, 2 neutres, 1 negative
echo.
echo ================================================================================
echo.
echo  MENU PRINCIPAL : MENU_PUBLICATIONS.cmd
echo.
echo  DOCUMENTATION : GUIDE_PUBLICATIONS_SENTIMENT.md
echo.
echo  SCHEMA VISUEL : SCHEMA_SYSTEME_PUBLICATIONS.txt
echo.
echo ================================================================================
echo.
pause
