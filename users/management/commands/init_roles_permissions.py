"""
Management command pour initialiser les rôles et permissions par défaut
Usage: python manage.py init_roles_permissions
"""

from django.core.management.base import BaseCommand
from users.models import Role, Permission, RolePermission


class Command(BaseCommand):
    help = 'Initialise les rôles et permissions de la plateforme selon le diagramme de cas d\'utilisation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('Initialisation des Rôles et Permissions'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        # 1. CRÉER LES PERMISSIONS
        self.stdout.write('\n📋 Création des permissions...')
        
        permissions_data = [
            # Accès aux données
            {'code': 'data.view_all', 'name': 'Visualiser toutes les données', 'category': Permission.DATA_ACCESS},
            {'code': 'data.view_dashboard', 'name': 'Accéder aux tableaux de bord', 'category': Permission.DATA_ACCESS},
            {'code': 'data.view_kpi', 'name': 'Consulter les KPI', 'category': Permission.DATA_ACCESS},
            {'code': 'data.search_indicators', 'name': 'Rechercher des indicateurs', 'category': Permission.DATA_ACCESS},
            {'code': 'data.view_brvm', 'name': 'Accéder aux données BRVM', 'category': Permission.DATA_ACCESS},
            {'code': 'data.view_worldbank', 'name': 'Accéder aux données WorldBank', 'category': Permission.DATA_ACCESS},
            {'code': 'data.view_imf', 'name': 'Accéder aux données IMF', 'category': Permission.DATA_ACCESS},
            
            # Export de données
            {'code': 'export.csv', 'name': 'Exporter en CSV', 'category': Permission.DATA_EXPORT},
            {'code': 'export.excel', 'name': 'Exporter en Excel', 'category': Permission.DATA_EXPORT},
            {'code': 'export.json', 'name': 'Exporter en JSON', 'category': Permission.DATA_EXPORT},
            
            # Ingestion de données
            {'code': 'ingestion.trigger', 'name': 'Déclencher une ingestion', 'category': Permission.DATA_INGESTION},
            {'code': 'ingestion.schedule', 'name': 'Planifier des ingestions', 'category': Permission.DATA_INGESTION},
            {'code': 'ingestion.monitor', 'name': 'Surveiller les ingestions', 'category': Permission.DATA_INGESTION},
            {'code': 'ingestion.retry', 'name': 'Relancer un job échoué', 'category': Permission.DATA_INGESTION},
            
            # Configuration admin
            {'code': 'admin.manage_users', 'name': 'Gérer les utilisateurs', 'category': Permission.ADMIN_CONFIG},
            {'code': 'admin.manage_roles', 'name': 'Gérer les rôles et permissions', 'category': Permission.ADMIN_CONFIG},
            {'code': 'admin.configure_sources', 'name': 'Configurer les sources de données', 'category': Permission.ADMIN_CONFIG},
            {'code': 'admin.view_audit', 'name': 'Consulter les logs d\'audit', 'category': Permission.ADMIN_CONFIG},
            
            # Gestion pipelines
            {'code': 'pipeline.create', 'name': 'Créer un pipeline', 'category': Permission.PIPELINE_MANAGE},
            {'code': 'pipeline.edit', 'name': 'Modifier un pipeline', 'category': Permission.PIPELINE_MANAGE},
            {'code': 'pipeline.delete', 'name': 'Supprimer un pipeline', 'category': Permission.PIPELINE_MANAGE},
            {'code': 'pipeline.run', 'name': 'Exécuter un pipeline', 'category': Permission.PIPELINE_MANAGE},
            {'code': 'pipeline.validate', 'name': 'Valider la qualité des données', 'category': Permission.PIPELINE_MANAGE},
            
            # API
            {'code': 'api.read', 'name': 'Lire via API', 'category': Permission.API_CONSUME},
            {'code': 'api.write', 'name': 'Écrire via API', 'category': Permission.API_CONSUME},
            
            # Audit
            {'code': 'audit.view', 'name': 'Voir les logs d\'audit', 'category': Permission.AUDIT_VIEW},
            {'code': 'audit.export', 'name': 'Exporter les logs d\'audit', 'category': Permission.AUDIT_VIEW},
        ]
        
        for perm_data in permissions_data:
            perm, created = Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'category': perm_data['category']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {perm.code}'))
        
        # 2. CRÉER LES RÔLES
        self.stdout.write('\n👥 Création des rôles...')
        
        roles_data = [
            {
                'code': Role.ADMIN_PLATFORM,
                'name': 'Administrateur Plateforme',
                'description': 'Accès complet: configure les sources, gère les utilisateurs, supervise la plateforme'
            },
            {
                'code': Role.DATA_ENGINEER,
                'name': 'Ingénieur Data/ETL',
                'description': 'Gère les pipelines ETL, ingestion, qualité des données'
            },
            {
                'code': Role.ANALYST_ECONOMIST,
                'name': 'Analyste/Économiste',
                'description': 'Explore, visualise et exporte les données pour analyses'
            },
            {
                'code': Role.READER_STAKEHOLDER,
                'name': 'Lecteur (Stakeholder)',
                'description': 'Consultation simple des dashboards et exports'
            },
            {
                'code': Role.API_CLIENT,
                'name': 'Client API Externe',
                'description': 'Accès programmatique via API REST'
            },
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {role.name}'))
        
        # 3. ASSOCIER LES PERMISSIONS AUX RÔLES
        self.stdout.write('\n🔗 Association rôles ↔ permissions...')
        
        # Supprimer les anciennes associations
        RolePermission.objects.all().delete()
        
        # Définir les associations
        role_permissions_mapping = {
            Role.ADMIN_PLATFORM: [
                'data.view_all', 'data.view_dashboard', 'data.view_kpi', 'data.search_indicators',
                'data.view_brvm', 'data.view_worldbank', 'data.view_imf',
                'export.csv', 'export.excel', 'export.json',
                'ingestion.trigger', 'ingestion.schedule', 'ingestion.monitor', 'ingestion.retry',
                'admin.manage_users', 'admin.manage_roles', 'admin.configure_sources', 'admin.view_audit',
                'pipeline.create', 'pipeline.edit', 'pipeline.delete', 'pipeline.run', 'pipeline.validate',
                'audit.view', 'audit.export',
            ],
            Role.DATA_ENGINEER: [
                'data.view_all', 'data.view_dashboard',
                'export.csv', 'export.json',
                'ingestion.trigger', 'ingestion.schedule', 'ingestion.monitor', 'ingestion.retry',
                'pipeline.create', 'pipeline.edit', 'pipeline.delete', 'pipeline.run', 'pipeline.validate',
                'audit.view',
            ],
            Role.ANALYST_ECONOMIST: [
                'data.view_all', 'data.view_dashboard', 'data.view_kpi', 'data.search_indicators',
                'data.view_brvm', 'data.view_worldbank', 'data.view_imf',
                'export.csv', 'export.excel', 'export.json',
            ],
            Role.READER_STAKEHOLDER: [
                'data.view_dashboard', 'data.view_kpi',
                'export.csv',
            ],
            Role.API_CLIENT: [
                'api.read',
                'data.view_all',
            ],
        }
        
        for role_code, perm_codes in role_permissions_mapping.items():
            role = Role.objects.get(code=role_code)
            self.stdout.write(f'\n  {role.name}:')
            
            for perm_code in perm_codes:
                try:
                    permission = Permission.objects.get(code=perm_code)
                    RolePermission.objects.create(role=role, permission=permission)
                    self.stdout.write(f'    ✓ {perm_code}')
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'    ✗ {perm_code} (permission not found)'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ Initialisation terminée!'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        # Afficher un résumé
        self.stdout.write(f'\n📊 Résumé:')
        self.stdout.write(f'  • Rôles créés: {Role.objects.count()}')
        self.stdout.write(f'  • Permissions créées: {Permission.objects.count()}')
        self.stdout.write(f'  • Associations créées: {RolePermission.objects.count()}')
