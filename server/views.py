from django.db.models import Count
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Server
from .schema import server_list_docs
from .serializer import ServerSerializer


class ServerListViewSet(viewsets.ViewSet):
    queryset = Server.objects.all()
    # permission_classes = [IsAuthenticated]
     
    @server_list_docs
    def list(self, request):
        """
        Filtra e retorna uma lista de servidores com base nos parâmetros de consulta fornecidos.

        Args:
        request: O objeto de solicitação HTTP contendo parâmetros de consulta. Os parâmetros de consulta suportados incluem:

        - `category (str)`: Opcional. Filtra servidores pelo nome da categoria.
        - `qty (int)`: Opcional. Limita o número de servidores retornados.
        - `by_user (str)`: Opcional. Se "true", filtra servidores pelo usuário autenticado.
        - `by_serverid (str)`: Opcional. Filtra servidores pelo ID do servidor.
        - `with_num_members (str)`: Opcional. Se "true", inclui o número de membros na resposta.

        Raises:
        AuthenticationFailed: Se `by_user` é "true" e o usuário não está autenticado.
        ValidationError: Se `by_serverid` é fornecido mas nenhum servidor com tal ID existe, ou se há um erro de valor de servidor.

        Returns:
        Response: Um objeto de resposta do Django REST framework contendo dados de servidores serializados.
            Se `with_num_members` é "true", o número de membros é incluído na resposta.

        Notas:
        - As exceções `AuthenticationFailed` e `ValidationError` fazem parte das exceções do Django REST framework.
        - Este método assume que é um método de uma classe que tem `queryset` e `ServerSerializer` disponíveis.
        - O método atualiza `self.queryset` com base nos filtros aplicados.
        """
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"

        # if by_user and not request.user.is_authenticated:
        #     raise AuthenticationFailed()

        if category:
            self.queryset = self.queryset.filter(category__name=category)

        if by_user:
            if by_user and request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)
            else:
                raise AuthenticationFailed()

        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        if qty:
            self.queryset = self.queryset[: int(qty)]

        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()
            
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server with id {by_serverid} not found")

            except ValueError:
                raise ValidationError(detail=f"Server value error")
        


        serializer = ServerSerializer(self.queryset, many=True, context={"num_members": with_num_members})
        return Response(serializer.data)