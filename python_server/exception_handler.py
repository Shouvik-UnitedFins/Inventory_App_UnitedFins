from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # If DRF generated a response, wrap the error in a 'message' field
        if isinstance(response.data, dict):
            # If 'detail' key exists, use it as the message
            if 'detail' in response.data:
                response.data = {'message': response.data['detail']}
            # If it's a validation error, join all messages
            elif any(isinstance(v, list) for v in response.data.values()):
                messages = []
                for v in response.data.values():
                    if isinstance(v, list):
                        messages.extend([str(i) for i in v])
                    else:
                        messages.append(str(v))
                response.data = {'message': ' '.join(messages)}
            else:
                response.data = {'message': str(response.data)}
        else:
            response.data = {'message': str(response.data)}
        return response

    # For exceptions that DRF does not handle, return a generic error
    return Response({'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
