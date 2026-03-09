from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/push/register/', views.register_push_token_api, name='register_push_token_api'),
    path('brvm/', views.dashboard_brvm, name='dashboard_brvm'),
    path('brvm/publications/', views.brvm_publications_page, name='brvm_publications_page'),
    path('worldbank/', views.dashboard_worldbank, name='dashboard_worldbank'),
    path('imf/', views.dashboard_imf, name='dashboard_imf'),
    path('un/', views.dashboard_un, name='dashboard_un'),
    path('afdb/', views.dashboard_afdb, name='dashboard_afdb'),
    path('explorer/', views.explorer, name='explorer'),
    path('comparateur/', views.comparateur, name='comparateur'),
    path('administration/', views.administration, name='administration'),
    path('recherche/', views.global_search, name='global_search'),
    path('exportpdf/<str:source>', views.export_dashboard_pdf, name='export_dashboard_pdf'), 
    path('exportexcel/<str:source>', views.export_dashboard_excel, name='export_dashboard_excel'), 
    path('export_csv/<str:source>', views.export_dashboard_csv, name='export_dashboard_csv'),
    
    # API BRVM
    path('api/brvm/summary/', views.brvm_summary_api, name='brvm_summary_api'),
    path('api/brvm/stocks/', views.brvm_stocks_api, name='brvm_stocks_api'),
    path('api/brvm/stock/<str:symbol>/', views.brvm_stock_detail_api, name='brvm_stock_detail_api'),
    path('api/brvm/candlestick/', views.brvm_candlestick_api, name='brvm_candlestick_api'),
    path('api/brvm/winners-losers/', views.brvm_winners_losers_api, name='brvm_winners_losers_api'),
    path('api/brvm/publications/', views.brvm_publications_api, name='brvm_publications_api'),
    path('api/brvm/publications/export/', views.export_brvm_publications, name='export_brvm_publications'),
    
    # API Recommandations & Analyse Prédictive
    path('brvm/recommendations/', views.brvm_recommendations_page, name='brvm_recommendations_page'),
    path('api/brvm/recommendations/', views.brvm_recommendations_api, name='brvm_recommendations_api'),
    path('api/brvm/recommendations/ia/', views.brvm_recommendations_ia_api, name='brvm_recommendations_ia_api'),
    path('api/brvm/stock/<str:symbol>/analysis/', views.brvm_stock_analysis_api, name='brvm_stock_analysis_api'),
    path('api/brvm/portfolio/suggestions/', views.brvm_portfolio_suggestions_api, name='brvm_portfolio_suggestions_api'),
    path('api/brvm/performance/', views.brvm_performance_report_api, name='brvm_performance_report_api'),
    
    # Prédictions IA (ML/Deep Learning)
    path('predictions/', views.predictions_page, name='predictions_page'),
    path('api/predictions/<str:symbol>/', views.stock_prediction_api, name='stock_prediction_api'),
    path('api/predictions/batch/', views.batch_predictions_api, name='batch_predictions_api'),
    
    # Data Marketplace - Téléchargement de données
    path('marketplace/', views.data_marketplace_page, name='data_marketplace_page'),
    path('marketplace/prepare/', views.prepare_download, name='prepare_download'),
    path('marketplace/download/', views.download_data, name='download_data'),
    path('marketplace/get-years/', views.get_available_years, name='get_available_years'),
    path('marketplace/get-datasets/', views.get_available_datasets, name='get_available_datasets'),
    path('marketplace/api-docs/', views.api_documentation, name='api_documentation'),
]
