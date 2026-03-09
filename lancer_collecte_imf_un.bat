@echo off
echo Lancement collecte IMF + UN SDG...
cd /d "E:\DISQUE C\Desktop\Implementation plateforme"
python collecter_imf_un_completion.py > collecte_imf_un_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log 2>&1
echo Collecte terminee.
pause
