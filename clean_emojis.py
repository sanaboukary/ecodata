import re

# Lire et nettoyer le fichier
with open('restauration_brvm_production.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Supprimer emojis et caractères spéciaux
content = content.replace('️', '').replace('⃣', '')
content = content.replace('✅', 'OK').replace('❌', 'ERREUR')
content = content.replace('⚠️', 'ATTENTION').replace('🔄', '')
content = content.replace('📊', '').replace('🚀', '')

# Sauvegarder
with open('restauration_brvm_production.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Script nettoye - emojis supprimes")
