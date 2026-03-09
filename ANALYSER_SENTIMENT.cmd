@echo off
title Analyse Sentiment Publications BRVM
color 0E

echo ===============================================================================
echo            ANALYSEUR DE SENTIMENT - PUBLICATIONS BRVM
echo ===============================================================================
echo.
echo  Analyse intelligente des publications pour aide a la decision :
echo  - Sentiment positif/negatif/neutre
echo  - Detection d'evenements financiers (resultats, dividendes)
echo  - Score d'impact sur cours de bourse
echo  - Signal trading BUY/HOLD/SELL
echo.
echo ===============================================================================
echo.

choice /C 123 /M "Choisissez : [1] Analyser toutes (30 jours)  [2] Analyser 7 jours  [3] Score par emetteur"

if errorlevel 3 goto EMETTEUR
if errorlevel 2 goto WEEK
if errorlevel 1 goto MONTH

:MONTH
echo.
echo  Analyse des publications des 30 derniers jours...
echo.
python analyser_sentiment_publications.py --days 30
goto END

:WEEK
echo.
echo  Analyse des publications des 7 derniers jours...
echo.
python analyser_sentiment_publications.py --days 7
goto END

:EMETTEUR
echo.
echo  Exemples : SNTS, BOABF, BICC, ECOC, SGBC, BRVM
echo.
set /p EMETTEUR="Entrez le code emetteur : "
echo.
python analyser_sentiment_publications.py --emetteur %EMETTEUR%
goto END

:END
echo.
echo ===============================================================================
echo  Dashboard : http://127.0.0.1:8000/brvm/publications/
echo ===============================================================================
echo.
pause
