from django.shortcuts import render
from plateforme_centralisation.mongo import get_mongo_db

def classement_objectif(request):
    db = get_mongo_db()
    objectif = request.GET.get("objectif", "TRADING")
    data = list(db.classements_brvm.find({
        "objectif": objectif
    }).sort("rank", 1))
    return render(request, "classement.html", {
        "data": data,
        "objectif": objectif
    })
