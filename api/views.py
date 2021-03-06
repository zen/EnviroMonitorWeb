from django.core.cache import cache
from rest_framework import response, schemas
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.decorators import detail_route
from rest_framework.permissions import AllowAny
from rest_framework.settings import api_settings
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ModelViewSet
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from .exceptions import StationWrongToken
from .filters import StationFilterSet, MeteringFilterSet, MeteringHistoryFilterSet, ProjectFilterSet
from .models import Station, Metering, MeteringHistory, Project
from .serializers import StationSerializer, MeteringSerializer, MeteringHistorySerializer, ProjectSerializer


class ObtainJWT(ObtainJSONWebToken):
    authentication_classes = (BasicAuthentication,)


class StationViewSet(ModelViewSet):
    """ViewSet for the Station class"""

    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS + [InBBoxFilter]
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    filter_class = StationFilterSet
    ordering_fields = ('updated', 'created', 'name')
    bbox_filter_field = 'position'

    @detail_route(methods=['post'], permission_classes=[AllowAny], url_path='add-metering')
    def add_metering(self, request, pk=None):
        station = self.get_object()
        request_token = request.query_params.get('token')
        if request_token is None or station.token != request_token:
            raise StationWrongToken

        metering_serializer = MeteringSerializer(data=request.data)
        if metering_serializer.is_valid():
            # create Metering from selected station and provided data
            Metering.objects.create(station=station, **metering_serializer.data)
            # remove last_metering cache key
            cache.delete(station.last_metering_cache_key)
            return response.Response({
                'status': 'metering added'
            })

        return response.Response(
            metering_serializer.errors,
            status=HTTP_400_BAD_REQUEST
        )


class MeteringViewSet(ModelViewSet):
    """ViewSet for the Metering class"""

    queryset = Metering.objects.all()
    serializer_class = MeteringSerializer
    filter_class = MeteringFilterSet
    ordering_fields = ('created',)


class MeteringHistoryViewSet(ModelViewSet):
    """ViewSet for the MeteringHistory class"""

    queryset = MeteringHistory.objects.all()
    serializer_class = MeteringHistorySerializer
    filter_class = MeteringHistoryFilterSet
    ordering_fields = ('created',)


class ProjectViewSet(ModelViewSet):
    """ViewSet for the Project class"""

    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS + [InBBoxFilter]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_class = ProjectFilterSet
    ordering_fields = ('updated', 'created', 'name')
    bbox_filter_field = 'position'


@api_view()
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Air Monitor REST API')
    return response.Response(generator.get_schema(request=request))

