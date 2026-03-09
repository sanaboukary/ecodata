#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nettoyer tous les emojis du fichier pipeline_weekly.py
"""
import re

file_path = "brvm_pipeline/pipeline_weekly.py"

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacements emoji -> texte
replacements = {
    '🔵': '>>',
    '📊': '[DATA]',
    '📅': '[DATE]',
    '✅': 'OK',
    '⚠️': 'ATTENTION',
    '🔥': '[!]',
    '⃣': '',
    '️': ''
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Supprimer tous les autres emojis restants (Unicode ranges)
# Emojis are typically in these ranges
emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)

content = emoji_pattern.sub('', content)

# Écrire le fichier nettoyé
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fichier nettoye: {file_path}")
print("Tous les emojis ont ete supprimes")
