"""
Commande Django pour initialiser les rôles et permissions de la plateforme
Basé sur le diagramme de cas d'utilisation avec 8 acteurs

Usage:
    python manage.py init_roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Role, Permission


User = get_user_model()


class Command(BaseCommand):
    help = 'Initialise les rôles et permissions de la plateforme'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('INITIALISATION DES RÔLES ET PERMISSIONS'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        # Définition des permissions par catégorie
        permissions_config = self.get_permissions_config()
        
        # Créer les permissions
        created_perms = self.create_permissions(permissions_config)
        
        # Définition des rôles et leurs permissions
        roles_config = self.get_roles_config()
        
        # Créer les rôles
        created_roles = self.create_roles(roles_config, created_perms)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS(f'✓ {len(created_perms)} permissions créées'))
        self.stdout.write(self.style.SUCCESS(f'✓ {len(created_roles)} rôles créés'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        # Afficher le résumé
        self.display_summary(created_roles, created_perms)
    
    def get_permissions_config(self):
        """Configuration des permissions par catégorie"""
        return {
            # ACCÈS AUX DONNÉES
            'data_access': [
                ('view_brvm_data', 'Consulter données BRVM'),
                ('view_worldbank_data', 'Consulter données Banque Mondiale'),
                ('view_imf_data', 'Consulter données FMI'),
                ('view_un_data', 'Consulter données ONU'),
                ('view_afdb_data', 'Consulter données BAD'),
                ('view_all_sources', 'Consulter toutes les sources'),
            ],
            
            # EXPORT DE DONNÉES
            'data_export': [
                ('export_csv', 'Exporter en CSV'),
                ('export_excel', 'Exporter en Excel'),
                ('export_json', 'Exporter en JSON'),
                ('export_api', 'Accès API REST'),
            ],
            
            # INGESTION DE DONNÉES
            'data_ingestion': [
                ('run_manual_ingestion', 'Lancer collecte manuelle'),
                ('schedule_ingestion', 'Planifier collectes'),
                ('stop_ingestion', 'Arrêter collectes'),
                ('retry_failed_jobs', 'Relancer jobs échoués'),
            ],
            
            # GESTION DES SOURCES
            'source_management': [
                ('add_data_source', 'Ajouter une source'),
                ('edit_data_source', 'Modifier une source'),
                ('delete_data_source', 'Supprimer une source'),
                ('configure_source', 'Configurer source'),
            ],
            
            # ADMINISTRATION
            'admin': [
                ('manage_users', 'Gérer les utilisateurs'),
                ('manage_roles', 'Gérer les rôles'),
                ('view_audit_logs', 'Consulter logs audit'),
                ('manage_permissions', 'Gérer permissions'),
                ('system_configuration', 'Configuration système'),
            ],
            
            # MONITORING & QUALITÉ
            'monitoring': [
                ('view_pipelines', 'Voir les pipelines'),
                ('monitor_jobs', 'Surveiller les jobs'),
                ('view_data_quality', 'Voir qualité données'),
                ('receive_alerts', 'Recevoir alertes'),
            ],
            
            # VISUALISATION
            'visualization': [
                ('access_dashboards', 'Accéder aux dashboards'),
                ('create_dashboards', 'Créer dashboards'),
                ('share_dashboards', 'Partager dashboards'),
            ],
        }
    
    def get_roles_config(self):
        """Configuration des rôles et leurs permissions"""
        return {
            Role.ADMIN_PLATFORM: {
                'name': 'Administrateur Plateforme',
                'description': '''
                    Rôle super-utilisateur avec tous les droits.
                    Responsable de:
                    - Configuration des sources de données
                    - Gestion des rôles et accès (RBAC)
                    - Supervision de la plateforme (audit, incidents)
                    - Planification des collectes automatisées
                ''',
                'permissions': [
                    # Accès total
                    'view_all_sources',
                    'export_csv', 'export_excel', 'export_json', 'export_api',
                    'run_manual_ingestion', 'schedule_ingestion', 'stop_ingestion', 'retry_failed_jobs',
                    'add_data_source', 'edit_data_source', 'delete_data_source', 'configure_source',
                    'manage_users', 'manage_roles', 'view_audit_logs', 'manage_permissions', 'system_configuration',
                    'view_pipelines', 'monitor_jobs', 'view_data_quality', 'receive_alerts',
                    'access_dashboards', 'create_dashboards', 'share_dashboards',
                ]
            },
            
            Role.DATA_ENGINEER: {
                'name': 'Ingénieur Data/ETL',
                'description': '''
                    Responsable technique des pipelines de données.
                    Responsable de:
                    - Mise en place des pipelines ETL
                    - Contrôle qualité des données
                    - Gestion de l'ingestion (API, fichiers, scraping)
                    - Relance des jobs en échec
                    - Optimisation du stockage
                ''',
                'permissions': [
                    'view_all_sources',
                    'export_csv', 'export_json',
                    'run_manual_ingestion', 'schedule_ingestion', 'stop_ingestion', 'retry_failed_jobs',
                    'configure_source',
                    'view_audit_logs',
                    'view_pipelines', 'monitor_jobs', 'view_data_quality', 'receive_alerts',
                    'access_dashboards',
                ]
            },
            
            Role.ANALYST_ECONOMIST: {
                'name': 'Analyste/Économiste',
                'description': '''
                    Utilisateur métier qui analyse les données économiques.
                    Responsable de:
                    - Recherche et exploration des indicateurs
                    - Visualisation via dashboards interactifs
                    - Export des résultats pour analyses
                    - Consultation des KPI par source
                ''',
                'permissions': [
                    'view_all_sources',
                    'export_csv', 'export_excel', 'export_json',
                    'access_dashboards', 'create_dashboards',
                ]
            },
            
            Role.READER_STAKEHOLDER: {
                'name': 'Lecteur (Stakeholder)',
                'description': '''
                    Consommateur simple des données (investisseur, décideur, bailleur).
                    Responsable de:
                    - Consultation de dashboards
                    - Accès à une vision synthétique
                    - Pas de manipulation de données brutes
                ''',
                'permissions': [
                    'view_all_sources',
                    'access_dashboards',
                ]
            },
            
            Role.API_CLIENT: {
                'name': 'Client API Externe',
                'description': '''
                    Système ou application externe connecté via API.
                    Responsable de:
                    - Interrogation des endpoints REST
                    - Consommation des données via API
                    - Exemple: Dashboard Power BI, application mobile
                ''',
                'permissions': [
                    'view_all_sources',
                    'export_api',
                ]
            },
        }
    
    def create_permissions(self, config):
        """Crée toutes les permissions"""
        created = {}
        
        self.stdout.write('\n📋 Création des permissions...')
        
        for category, perms in config.items():
            for code, name in perms:
                perm, created_flag = Permission.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'category': category,
                        'description': f'Permission: {name}'
                    }
                )
                created[code] = perm
                status = '✓ Créée' if created_flag else '  Existe'
                self.stdout.write(f'  {status}: {code} ({name})')
        
        return created
    
    def create_roles(self, config, permissions):
        """Crée tous les rôles avec leurs permissions"""
        created = {}
        
        self.stdout.write('\n👥 Création des rôles...')
        
        for role_code, role_data in config.items():
            role, created_flag = Role.objects.get_or_create(
                code=role_code,
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'].strip(),
                }
            )
            
            # Assigner les permissions
            role_perms = [permissions[p] for p in role_data['permissions'] if p in permissions]
            role.permissions.set(role_perms)
            
            created[role_code] = role
            status = '✓ Créé' if created_flag else '  Mis à jour'
            self.stdout.write(f'  {status}: {role.name} ({len(role_perms)} permissions)')
        
        return created
    
    def display_summary(self, roles, permissions):
        """Affiche un résumé de la configuration"""
        self.stdout.write('\n📊 RÉSUMÉ DE LA CONFIGURATION\n')
        
        for role_code, role in roles.items():
            self.stdout.write(self.style.WARNING(f'\n{role.name.upper()}'))
            self.stdout.write('-' * 80)
            
            # Description
            desc_lines = role.description.strip().split('\n')
            for line in desc_lines[:3]:  # Premières lignes seulement
                self.stdout.write(f'  {line.strip()}')
            
            # Permissions
            perms = role.permissions.all()
            self.stdout.write(f'\n  📋 Permissions ({perms.count()}):')
            
            # Grouper par catégorie
            by_category = {}
            for p in perms:
                by_category.setdefault(p.category, []).append(p.name)
            
            for cat, perm_names in sorted(by_category.items()):
                cat_display = cat.replace('_', ' ').title()
                self.stdout.write(f'     • {cat_display}: {len(perm_names)} permission(s)')
