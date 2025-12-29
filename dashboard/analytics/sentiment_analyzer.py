"""
Analyseur de Sentiment pour les Publications BRVM
Extrait les signaux d'achat/vente des publications officielles
"""
import logging
import re
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PublicationSentimentAnalyzer:
    """Analyse le sentiment et extrait les signaux des publications BRVM"""
    
    def __init__(self):
        # Utiliser notre propre analyseur de sentiment basé sur les mots-clés
        
        # Mots-clés positifs avec poids
        self.positive_keywords = {
            'dividende': 30,
            'exceptionnel': 25,
            'augmentation': 20,
            'croissance': 20,
            'bénéfice': 25,
            'hausse': 20,
            'profit': 25,
            'progression': 20,
            'record': 30,
            'excellent': 25,
            'performance': 15,
            'solide': 15,
            'positif': 15,
            'succès': 20,
            'amélioration': 20,
            'consolidé': 15,
            'renforcement': 15,
            'expansion': 20,
            'acquisition': 15,
            'nouveau contrat': 25,
            'partenariat': 15,
        }
        
        # Mots-clés négatifs avec poids
        self.negative_keywords = {
            'suspension': -30,
            'perte': -25,
            'baisse': -20,
            'déficit': -25,
            'dette': -15,
            'difficultés': -20,
            'crise': -25,
            'recul': -20,
            'chute': -25,
            'avertissement': -20,
            'alerte': -20,
            'risque': -15,
            'préoccupation': -15,
            'négatif': -15,
            'dégradation': -20,
            'restructuration': -10,
            'licenciement': -20,
            'fermeture': -25,
            'faillite': -30,
        }
        
        # Patterns pour extraire les chiffres
        self.number_patterns = {
            'percentage': r'([\+\-]?\d+[.,]?\d*)\s*%',
            'fcfa': r'(\d+(?:[.,]\d+)?)\s*(?:FCFA|F\s*CFA|francs)',
            'million': r'(\d+[.,]?\d*)\s*millions?',
            'milliard': r'(\d+[.,]?\d*)\s*milliards?',
        }
    
    def analyze_publication(self, title: str, description: str = "", 
                          category: str = "") -> Dict[str, any]:
        """
        Analyse une publication et retourne un score de sentiment
        
        Returns:
            {
                'sentiment_score': -100 à +100,
                'sentiment_label': 'VERY_POSITIVE'|'POSITIVE'|'NEUTRAL'|'NEGATIVE'|'VERY_NEGATIVE',
                'confidence': 0-100,
                'extracted_numbers': {},
                'key_signals': [],
                'trading_signal': 'BUY'|'SELL'|'HOLD',
                'impact_level': 'HIGH'|'MEDIUM'|'LOW'
            }
        """
        try:
            # Combiner titre et description
            text = f"{title} {description}".lower()
            
            # 1. Analyse par mots-clés pondérés (remplace VADER)
            keyword_score = 0
            detected_keywords = []
            
            # Compter les occurrences de chaque mot-clé
            for word, weight in self.positive_keywords.items():
                count = text.count(word)
                if count > 0:
                    keyword_score += weight * count
                    detected_keywords.append((word, weight * count))
            
            for word, weight in self.negative_keywords.items():
                count = text.count(word)
                if count > 0:
                    keyword_score += weight * count  # weight est déjà négatif
                    detected_keywords.append((word, weight * count))
            
            # 2. Analyse spécifique par catégorie
            category_boost = self._analyze_category(category, text)
            
            # 3. Extraction de chiffres (bénéfices, dividendes, etc.)
            extracted_numbers = self._extract_numbers(text)
            numbers_boost = self._evaluate_numbers(extracted_numbers, text)
            
            # 4. Analyse de la structure grammaticale (phrases positives/négatives)
            structure_boost = self._analyze_structure(text)
            
            # 5. Calcul du score final (pondéré)
            final_score = (
                keyword_score * 0.50 +      # 50% mots-clés (principal)
                category_boost * 0.20 +     # 20% catégorie
                numbers_boost * 0.15 +      # 15% chiffres
                structure_boost * 0.15      # 15% structure
            )
            
            # Normaliser entre -100 et +100
            final_score = max(-100, min(100, final_score))
            
            # 6. Déterminer le label et le signal
            sentiment_label, trading_signal = self._get_labels(final_score)
            
            # 7. Calculer la confiance
            confidence = min(100, abs(final_score) * 0.8 + len(detected_keywords) * 3)
            
            # 8. Niveau d'impact
            impact_level = self._calculate_impact(
                final_score, 
                len(detected_keywords), 
                extracted_numbers
            )
            
            # 9. Signaux clés pour l'utilisateur
            key_signals = self._generate_key_signals(
                detected_keywords, 
                extracted_numbers, 
                trading_signal
            )
            
            return {
                'sentiment_score': round(final_score, 2),
                'sentiment_label': sentiment_label,
                'confidence': round(confidence, 1),
                'extracted_numbers': extracted_numbers,
                'key_signals': key_signals,
                'trading_signal': trading_signal,
                'impact_level': impact_level,
                'detected_keywords': [k[0] for k in detected_keywords],
                'keyword_score': keyword_score,
                'category_boost': category_boost,
                'numbers_boost': numbers_boost
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse sentiment: {e}")
            return self._neutral_result()
    
    def _analyze_category(self, category: str, text: str) -> float:
        """Boost selon la catégorie de publication"""
        category = category.lower()
        
        if 'dividende' in category:
            return 25  # Dividendes = très positif
        elif 'résultats' in category or 'financier' in category:
            # Dépend du contenu
            if 'hausse' in text or 'bénéfice' in text:
                return 20
            elif 'perte' in text or 'baisse' in text:
                return -20
        elif 'suspension' in category:
            return -25  # Suspension = très négatif
        elif 'assemblée' in category or 'ago' in category:
            return 5  # Neutre-positif
        elif 'fusion' in category or 'acquisition' in category:
            return 15  # Généralement positif
        
        return 0
    
    def _analyze_structure(self, text: str) -> float:
        """
        Analyse la structure grammaticale pour détecter le sentiment
        Sans NLP externe, on utilise des heuristiques simples
        """
        boost = 0
        
        # Mots de négation qui inversent le sentiment
        negations = ['pas', 'non', 'aucun', 'jamais', 'sans']
        has_negation = any(neg in text for neg in negations)
        
        # Phrases interrogatives (souvent neutres ou négatives)
        if '?' in text:
            boost -= 5
        
        # Exclamations (souvent émotionnelles)
        if '!' in text:
            boost += 5
        
        # Mots intensificateurs
        intensifiers = ['très', 'extrêmement', 'fortement', 'significatif', 'important']
        intensity_count = sum(1 for word in intensifiers if word in text)
        boost += intensity_count * 3
        
        # Comparaisons positives
        if any(phrase in text for phrase in ['mieux que', 'supérieur à', 'dépasse']):
            boost += 10
        
        # Comparaisons négatives
        if any(phrase in text for phrase in ['pire que', 'inférieur à', 'en dessous']):
            boost -= 10
        
        return boost
    
    def _extract_numbers(self, text: str) -> Dict[str, List[float]]:
        """Extrait les chiffres importants du texte"""
        numbers = {
            'percentages': [],
            'amounts_fcfa': [],
            'millions': [],
            'milliards': []
        }
        
        # Pourcentages
        for match in re.finditer(self.number_patterns['percentage'], text):
            try:
                num = float(match.group(1).replace(',', '.'))
                numbers['percentages'].append(num)
            except:
                pass
        
        # Montants FCFA
        for match in re.finditer(self.number_patterns['fcfa'], text):
            try:
                num = float(match.group(1).replace(',', '.'))
                numbers['amounts_fcfa'].append(num)
            except:
                pass
        
        # Millions
        for match in re.finditer(self.number_patterns['million'], text):
            try:
                num = float(match.group(1).replace(',', '.'))
                numbers['millions'].append(num)
            except:
                pass
        
        # Milliards
        for match in re.finditer(self.number_patterns['milliard'], text):
            try:
                num = float(match.group(1).replace(',', '.'))
                numbers['milliards'].append(num)
            except:
                pass
        
        return numbers
    
    def _evaluate_numbers(self, numbers: Dict, text: str) -> float:
        """Évalue l'impact des chiffres extraits"""
        boost = 0
        
        # Pourcentages positifs
        for pct in numbers['percentages']:
            if pct > 0:
                if pct > 20:
                    boost += 20  # Très forte hausse
                elif pct > 10:
                    boost += 15
                elif pct > 5:
                    boost += 10
            elif pct < 0:
                if pct < -20:
                    boost -= 20
                elif pct < -10:
                    boost -= 15
                elif pct < -5:
                    boost -= 10
        
        # Gros montants = important
        if numbers['milliards']:
            boost += 10
        elif numbers['millions']:
            boost += 5
        
        return boost
    
    def _get_labels(self, score: float) -> Tuple[str, str]:
        """Retourne le label de sentiment et le signal de trading"""
        if score >= 50:
            return 'VERY_POSITIVE', 'STRONG_BUY'
        elif score >= 20:
            return 'POSITIVE', 'BUY'
        elif score >= -20:
            return 'NEUTRAL', 'HOLD'
        elif score >= -50:
            return 'NEGATIVE', 'SELL'
        else:
            return 'VERY_NEGATIVE', 'STRONG_SELL'
    
    def _calculate_impact(self, score: float, num_keywords: int, 
                         numbers: Dict) -> str:
        """Calcule le niveau d'impact de la publication"""
        impact_score = abs(score) + num_keywords * 5
        
        if numbers['milliards']:
            impact_score += 20
        elif numbers['millions']:
            impact_score += 10
        
        if impact_score >= 70:
            return 'HIGH'
        elif impact_score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_key_signals(self, keywords: List, numbers: Dict, 
                             signal: str) -> List[str]:
        """Génère les signaux clés pour l'utilisateur"""
        signals = []
        
        # Signal principal
        if signal in ['STRONG_BUY', 'BUY']:
            signals.append(f"📈 Signal d'ACHAT détecté")
        elif signal in ['STRONG_SELL', 'SELL']:
            signals.append(f"📉 Signal de VENTE détecté")
        
        # Mots-clés importants
        if keywords:
            top_keywords = sorted(keywords, key=lambda x: abs(x[1]), reverse=True)[:3]
            for word, weight in top_keywords:
                emoji = "✅" if weight > 0 else "⚠️"
                signals.append(f"{emoji} Mot-clé détecté: '{word}' (impact: {weight:+d})")
        
        # Chiffres significatifs
        if numbers['percentages']:
            for pct in numbers['percentages'][:2]:
                emoji = "📈" if pct > 0 else "📉"
                signals.append(f"{emoji} Variation: {pct:+.1f}%")
        
        if numbers['amounts_fcfa']:
            signals.append(f"💰 Montant: {numbers['amounts_fcfa'][0]:,.0f} FCFA")
        
        return signals
    
    def _neutral_result(self) -> Dict:
        """Résultat neutre en cas d'erreur"""
        return {
            'sentiment_score': 0,
            'sentiment_label': 'NEUTRAL',
            'confidence': 0,
            'extracted_numbers': {},
            'key_signals': [],
            'trading_signal': 'HOLD',
            'impact_level': 'LOW',
            'detected_keywords': [],
            'error': True
        }
    
    def analyze_publication_for_stock(self, stock_symbol: str, 
                                     publication_text: str) -> Dict:
        """
        Analyse si une publication concerne une action spécifique
        et retourne le sentiment associé
        """
        text_lower = publication_text.lower()
        symbol_lower = stock_symbol.lower()
        
        # Vérifier si l'action est mentionnée
        if symbol_lower not in text_lower:
            return None
        
        # Analyser la publication
        analysis = self.analyze_publication(publication_text, "", "")
        
        # Ajouter le symbole
        analysis['stock_symbol'] = stock_symbol
        analysis['is_relevant'] = True
        
        return analysis
