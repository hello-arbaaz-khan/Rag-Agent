from django.urls import path
from apps.rag.views import (DocumentListCreateView,DocumentStatusView,
    QuestionAnswer,DocumentDetailView,ChatHistoryView,SyncDrive,
    SearchView,ConnectDriveView,DriveConnectionStatusView,DisconnectDriveView)
    
urlpatterns = [
    path('upload/', DocumentListCreateView.as_view(), name='upload'),
    path('list/', DocumentListCreateView.as_view(), name='list'),
    path('detail/<int:document_id>/', DocumentDetailView.as_view(), name='detail'),
    path('status/<int:document_id>/', DocumentStatusView.as_view(), name='status'),
    path('question/', QuestionAnswer.as_view(), name='question'),
    path('history/<int:document_id>/', ChatHistoryView.as_view(), name='history'),
    path('sync-drive/', SyncDrive.as_view(), name='sync-drive'),
    path('search/', SearchView.as_view(), name='search'),
    path('connect-drive/', ConnectDriveView.as_view(), name='connect-drive'),
    path('drive-status/', DriveConnectionStatusView.as_view(), name='drive-status'),
    path('disconnect-drive/', DisconnectDriveView.as_view(), name='disconnect-drive'),
]
