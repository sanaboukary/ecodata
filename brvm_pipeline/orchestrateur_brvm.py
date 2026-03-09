
import os
import subprocess

PIPELINE = [
    "collecter_publications_brvm.py",
    "extraction_semantique_brvm.py",
    "agregateur_semantique_actions.py",
    "analyse_ia_simple.py",
    "auto_learning_brvm.py",
    "decision_finale_brvm.py"
]

python_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
pipeline_dir = os.path.dirname(__file__)
for script in PIPELINE:
    script_path = os.path.join(pipeline_dir, script)
    subprocess.run([
        python_exe, script_path
    ], check=True)

classement_script = os.path.join(pipeline_dir, "classement_brvm.py")
subprocess.run([
    python_exe, classement_script
], check=True)

print("✅ Pipeline BRVM exécuté avec succès et classement mis à jour")
