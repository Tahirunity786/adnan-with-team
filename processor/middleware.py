import logging
from typing import Any
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.auth import AuthMiddlewareStack
import json

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(token):
    try:
        user = get_user_model().objects.get(id=token['user_id'])
        return user
    except get_user_model().DoesNotExist:
        return AnonymousUser()

@database_sync_to_async
def get_interview_target(target_id):
    try:
        user = get_user_model().objects.get(id=target_id)
        return user
    except get_user_model().DoesNotExist:
        return AnonymousUser()

class JwtAuthForAsgi(BaseMiddleware):

    async def __call__(self, scope, receive, send) -> Any:
        close_old_connections()
        is_target_needed = "peersocket" in scope['path'] or "chat" in scope['path']

        token_query = parse_qs(scope['query_string'].decode("utf8"))
        token = token_query.get('token', [''])[0]

        if not token:
            logger.warning("Token is missing")
            response = {'error': 'Token is missing'}
            await send({
                'type': 'http.response.start',
                'status': 401,
                'headers': [(b'content-type', b'application/json')],
            })
            await send({
                'type': 'http.response.body',
                'body': json.dumps(response).encode('utf-8'),
            })
            return

        try:
            UntypedToken(token)
        except (InvalidToken, TokenError):
            logger.error("Invalid token")
            response = {'error': 'Invalid token'}
            await send({
                'type': 'http.response.start',
                'status': 401,
                'headers': [(b'content-type', b'application/json')],
            })
            await send({
                'type': 'http.response.body',
                'body': json.dumps(response).encode('utf-8'),
            })
            return 
        else:
            token_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope['user'] = await get_user(token_data)
            if is_target_needed:
                target_id = token_query.get('target', [''])[0]
                if not target_id:
                    logger.warning("Target ID is missing")
                    response = {'error': 'Target ID is missing'}
                    await send({
                        'type': 'http.response.start',
                        'status': 400,
                        'headers': [(b'content-type', b'application/json')],
                    })
                    await send({
                        'type': 'http.response.body',
                        'body': json.dumps(response).encode('utf-8'),
                    })
                    return

                target = await get_interview_target(target_id)
                if isinstance(target, AnonymousUser):
                    logger.error("Invalid target ID")
                    response = {'error': 'Invalid target ID'}
                    await send({
                        'type': 'http.response.start',
                        'status': 404,
                        'headers': [(b'content-type', b'application/json')],
                    })
                    await send({
                        'type': 'http.response.body',
                        'body': json.dumps(response).encode('utf-8'),
                    })
                    return
                else:
                    scope['target'] = target

        return await super().__call__(scope, receive, send)

def JwtAuthForAsgiStack(inner):
    return JwtAuthForAsgi(AuthMiddlewareStack(inner))
