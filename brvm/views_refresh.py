import subprocess
import sys
import os
from django.shortcuts import redirect

def refresh_pipeline_brvm(request):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python = sys.executable
    subprocess.run(
        [python, os.path.join(base, "brvm_pipeline", "orchestrateur_brvm.py")],
        check=True
    )
    return redirect("/brvm/recommendations/")
