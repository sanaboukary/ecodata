"""
ml_recommandation.py
Module pour l'entraînement et la prédiction de recommandations BRVM avec un modèle ML (RandomForest par défaut).
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

class MLRecommandeur:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False

    def features_labels_from_data(self, actions_data):
        # Extrait les features et labels à partir des données d'actions (exemple simplifié)
        X, y = [], []
        for a in actions_data:
            X.append([
                a.get('variation', 0),
                a.get('volatilite', 0),
                a.get('volume', 0),
                a.get('score_sectoriel', 0),
                a.get('dividend_yield', 0),
            ])
            # Label : 1 = BUY/STRONG BUY, 0 = HOLD, -1 = SELL
            rec = a.get('recommendation', 'HOLD')
            if 'BUY' in rec:
                y.append(1)
            elif 'SELL' in rec:
                y.append(-1)
            else:
                y.append(0)
        return np.array(X), np.array(y)

    def entrainer(self, actions_data):
        X, y = self.features_labels_from_data(actions_data)
        if len(X) < 10:
            print("Pas assez de données pour entraîner le modèle.")
            return
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        print(classification_report(y_test, y_pred))

    def predire(self, actions_data):
        if not self.is_trained:
            print("Le modèle n'est pas entraîné.")
            return actions_data
        X, _ = self.features_labels_from_data(actions_data)
        y_pred = self.model.predict(X)
        for i, a in enumerate(actions_data):
            if y_pred[i] == 1:
                a['ml_recommendation'] = 'ML_BUY'
            elif y_pred[i] == -1:
                a['ml_recommendation'] = 'ML_SELL'
            else:
                a['ml_recommendation'] = 'ML_HOLD'
        return actions_data
