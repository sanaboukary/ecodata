#!/usr/bin/env python3
"""Verification rapide des collectes en cours"""
import os
from datetime import datetime

def compter_lignes(fichier):
    """Compter lignes avec OK/ECHEC"""
    if not os.path.exists(fichier):
        return 0, 0
    
    try:
        with open(fichier, 'r', encoding='utf-8', errors='ignore') as f:
            contenu = f.read()
            ok = contenu.count('OK -')
            echec = contenu.count('ECHEC')
            return ok, echec
    except:
        return 0, 0

print("\n" + "="*80)
print(f"VERIFICATION COLLECTES - {datetime.now().strftime('%H:%M:%S')}")
print("="*80)

# IMF
imf_ok, imf_echec = compter_lignes('imf_collecte.log')
print(f"\n[IMF] 64 combinaisons attendues")
print(f"  Reussies  : {imf_ok:3d}")
print(f"  Echouees  : {imf_echec:3d}")
print(f"  Progression: {imf_ok + imf_echec:3d}/64 ({(imf_ok + imf_echec)/64*100:.1f}%)" if imf_ok + imf_echec > 0 else "  Progression: 0/64 (0.0%)")

# AfDB + UN
afdb_ok, afdb_echec = compter_lignes('afdb_un_collecte.log')
print(f"\n[AfDB + UN SDG] 96 combinaisons attendues")
print(f"  Reussies  : {afdb_ok:3d}")
print(f"  Echouees  : {afdb_echec:3d}")
print(f"  Progression: {afdb_ok + afdb_echec:3d}/96 ({(afdb_ok + afdb_echec)/96*100:.1f}%)" if afdb_ok + afdb_echec > 0 else "  Progression: 0/96 (0.0%)")

# Total
total_ok = imf_ok + afdb_ok
total_echec = imf_echec + afdb_echec
total_ops = 64 + 96

print("\n" + "="*80)
print(f"TOTAL (IMF + AfDB/UN)")
print(f"  Reussies  : {total_ok:4d}")
print(f"  Echouees  : {total_echec:4d}")
print(f"  Progression: {total_ok + total_echec:4d}/{total_ops} ({(total_ok + total_echec)/total_ops*100:.1f}%)")
print("="*80)
