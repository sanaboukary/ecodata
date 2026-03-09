"""
sentiment_multilingue.py
Module pour l'analyse de sentiment multilingue sur texte extrait de PDF (CamemBERT ou BERT multilingue).
"""

from transformers import pipeline

class SentimentMultilingue:
    def __init__(self, model_name='j-hartmann/emotion-english-distilroberta-base', device=-1):
        # Pour la prod, utiliser un modèle multilingue/français (ex: 'j-hartmann/emotion-english-distilroberta-base', 'tblard/tf-allocine', 'camembert-base')
        self.analyzer = pipeline('sentiment-analysis', model=model_name, device=device)

    def analyser_publication(self, texte):
        # Retourne un score de sentiment (ex: positif, négatif, neutre, score)
        try:
            result = self.analyzer(texte[:512])  # Limite à 512 tokens pour rapidité
            label = result[0]['label']
            score = result[0]['score']
            return {'sentiment_label': label, 'sentiment_score': score}
        except Exception as e:
            return {'sentiment_label': 'NEUTRE', 'sentiment_score': 0.0}

    def batch_analyse(self, textes):
        # Analyse une liste de textes
        return [self.analyser_publication(t) for t in textes]
