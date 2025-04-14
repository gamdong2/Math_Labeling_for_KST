from django.urls import path
from .views import UploadFileAPIView, GetResultAPIView, upload_page
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger UI를 위한 설정
schema_view = get_schema_view(
    openapi.Info(
        title="자동 라벨링 시스템 API",
        default_version="v1",
        description="자동 라벨링 시스템의 API 문서입니다.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@myapi.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
)

urlpatterns = [
    path("upload/", upload_page, name="upload_page"),  # HTML 페이지 렌더링
    path(
        "api/upload/", UploadFileAPIView.as_view(), name="upload_file"
    ),  # 파일 업로드 API
    path(
        "api/results/<str:file_name>/", GetResultAPIView.as_view(), name="get_result"
    ),  # 결과 조회 API
    path(
        "swagger/", schema_view.as_view(), name="swagger"
    ),  # Swagger UI 엔드포인트 추가
]
