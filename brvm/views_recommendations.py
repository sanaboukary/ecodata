from django.shortcuts import render
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta


def recommendations_brvm(request):
    db = get_mongo_db()
    
    # Lire le TOP 5 hebdomadaire classé
    top5 = list(
        db.top5_weekly_brvm.find(
            {},
            {"_id": 0}
        ).sort([("rank", 1)])
    )
    
    # Calculer les statistiques pour le header
    if top5:
        confiance_moyenne = round(sum(r.get('confidence', 0) for r in top5) / len(top5))
        potentiel_hebdo_moyen = round(sum(r.get('gain_attendu', 0) for r in top5) / len(top5), 1)
    else:
        confiance_moyenne = 0
        potentiel_hebdo_moyen = 0
    
    # Calculer taux de réussite des 7 derniers jours depuis track_record
    semaine_derniere = datetime.now() - timedelta(days=7)
    track_records = list(db.track_record_weekly.find({
        "fige_le": {"$gte": semaine_derniere}
    }))
    
    if track_records:
        total_recs = sum(len(tr.get('symbols', [])) for tr in track_records)
        gagnantes = sum(
            len([s for s in tr.get('resultats_reels', {}).values() 
                 if isinstance(s, dict) and s.get('gain_reel', 0) > 0])
            for tr in track_records
        )
        taux_reussite = round((gagnantes / total_recs * 100) if total_recs > 0 else 0)
    else:
        taux_reussite = 0
    
    # Nombre total de recommandations actives
    nb_recommandations = len(top5)
    
    # Date de génération
    date_generation = top5[0].get('selected_at', datetime.now()) if top5 else datetime.now()
    if isinstance(date_generation, str):
        try:
            date_generation = datetime.fromisoformat(date_generation.replace('Z', '+00:00'))
        except:
            date_generation = datetime.now()
    
    return render(
        request,
        "brvm/recommendations.html", 
        {
            "tradables": top5,  # TOP 5 recommandations
            "bloques": [],  # Pas de signaux bloqués dans TOP5
            "horizon": "SEMAINE",
            "nb_recommandations": nb_recommandations,
            "confiance_moyenne": confiance_moyenne,
            "potentiel_hebdo_moyen": potentiel_hebdo_moyen,
            "taux_reussite": taux_reussite,
            "date_generation": date_generation,
        }
    )
