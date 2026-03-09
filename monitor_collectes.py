#!/usr/bin/env python3
"""Monitoring temps reel des collectes"""
import time
import os
from datetime import datetime

def compter_lignes(fichier):
    """Compter lignes avec OK/ECHEC"""
    if not os.path.exists(fichier):
        return 0, 0, 0
    
    try:
        with open(fichier, 'r', encoding='utf-8', errors='ignore') as f:
            contenu = f.read()
            ok = contenu.count('OK -')
            echec = contenu.count('ECHEC')
            termine = 'RAPPORT FINAL' in contenu
            return ok, echec, termine
    except:
        return 0, 0, 0

def afficher_stats():
    """Afficher statistiques en temps reel"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("="*80)
    print(f"MONITORING COLLECTES - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    print()
    
    # World Bank
    # Le processus est dans un terminal VS Code, cherchons les logs possibles
    wb_files = ['collecte_test_wb.log', 'wb_collecte.log', 'collecte_wb_log.txt']
    wb_ok, wb_echec, wb_termine = 0, 0, False
    for f in wb_files:
        if os.path.exists(f):
            wb_ok, wb_echec, wb_termine = compter_lignes(f)
            break
    
    print(f"[WORLD BANK] 88 combinaisons attendues")
    print(f"  Reussies  : {wb_ok:3d}")
    print(f"  Echouees  : {wb_echec:3d}")
    print(f"  Progression: {wb_ok + wb_echec:3d}/88 ({(wb_ok + wb_echec)/88*100:.1f}%)")
    print(f"  Status    : {'TERMINE' if wb_termine else 'EN COURS'}")
    print()
    
    # IMF
    imf_ok, imf_echec, imf_termine = compter_lignes('imf_collecte.log')
    print(f"[IMF] 64 combinaisons attendues")
    print(f"  Reussies  : {imf_ok:3d}")
    print(f"  Echouees  : {imf_echec:3d}")
    print(f"  Progression: {imf_ok + imf_echec:3d}/64 ({(imf_ok + imf_echec)/64*100:.1f}%)" if imf_ok + imf_echec > 0 else "  Progression: 0/64 (0.0%)")
    print(f"  Status    : {'TERMINE' if imf_termine else 'EN COURS'}")
    print()
    
    # AfDB + UN
    afdb_ok, afdb_echec, afdb_termine = compter_lignes('afdb_un_collecte.log')
    print(f"[AfDB + UN SDG] 96 combinaisons attendues")
    print(f"  Reussies  : {afdb_ok:3d}")
    print(f"  Echouees  : {afdb_echec:3d}")
    print(f"  Progression: {afdb_ok + afdb_echec:3d}/96 ({(afdb_ok + afdb_echec)/96*100:.1f}%)" if afdb_ok + afdb_echec > 0 else "  Progression: 0/96 (0.0%)")
    print(f"  Status    : {'TERMINE' if afdb_termine else 'EN COURS'}")
    print()
    
    # Total
    total_ok = wb_ok + imf_ok + afdb_ok
    total_echec = wb_echec + imf_echec + afdb_echec
    total_ops = 88 + 64 + 96
    
    print("="*80)
    print(f"TOTAL")
    print(f"  Reussies  : {total_ok:4d}")
    print(f"  Echouees  : {total_echec:4d}")
    print(f"  Progression: {total_ok + total_echec:4d}/{total_ops} ({(total_ok + total_echec)/total_ops*100:.1f}%)")
    
    toutes_terminees = wb_termine and imf_termine and afdb_termine
    print(f"  Status    : {'TOUTES TERMINEES' if toutes_terminees else 'EN COURS'}")
    print("="*80)
    
    return toutes_terminees

def main():
    print("Demarrage monitoring...")
    print("Appuyez sur Ctrl+C pour arreter")
    time.sleep(2)
    
    try:
        while True:
            terminees = afficher_stats()
            
            if terminees:
                print("\nToutes les collectes sont terminees !")
                print("\nPour voir le resume complet:")
                print("  python resume_simple.py")
                break
            
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nMonitoring arrete")

if __name__ == '__main__':
    main()
