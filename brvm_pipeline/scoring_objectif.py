from brvm_pipeline.config_objectifs import OBJECTIFS

def score_par_objectif(features, objectif):
    w = OBJECTIFS[objectif]["weights"]
    score = 0
    for facteur, poids in w.items():
        score += features.get(facteur, 0) * poids
    return round(score, 2)
