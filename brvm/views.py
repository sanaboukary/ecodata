import subprocess
import sys
import os
from django.http import JsonResponse

def run_brvm_pipeline(request):
    try:
        python_path = sys.executable
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "brvm_pipeline",
            "orchestrateur_brvm.py"
        )
        subprocess.run(
            [python_path, script_path],
            check=True
        )
        return JsonResponse({
            "status": "success",
            "message": "Pipeline BRVM exécuté avec succès"
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
from plateforme_centralisation.mongo import get_mongo_db
from django.shortcuts import render

def recommendations_view(request):
    # db = get_mongo_db()
    # horizon = request.GET.get("horizon", "SEMAINE")
    # decisions = list(db.decisions_finales_brvm.find(
    #     {"horizon": horizon},
    #     {"_id": 0}
    # ).sort("score", -1))
    # return render(request, "recommendations.html", {"decisions": decisions, "horizon": horizon})
    # LOGIQUE OBSOLÈTE COMMENTÉE : calcul signal, lecture autre collection, etc.
    return render(request, "recommendations.html", {"decisions": [], "horizon": None})
import subprocess
import sys
import os
from django.shortcuts import redirect
from django.contrib import messages

def refresh_brvm_pipeline(request):
    if request.method == "POST":
        try:
            python_exe = sys.executable
            script_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "brvm_pipeline",
                "orchestrateur_brvm.py"
            )
            subprocess.run([
                python_exe, script_path
            ], check=True)
            messages.success(request, "Pipeline BRVM exécuté avec succès")
        except Exception as e:
            messages.error(request, f"Erreur pipeline BRVM : {str(e)}")
    return redirect("brvm_recommendations")
