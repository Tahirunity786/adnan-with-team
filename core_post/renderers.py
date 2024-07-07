from rest_framework import renderers
import json

class UserRenderer(renderers.JSONRenderer):
    """
    Custom JSON renderer for handling User-related responses.

    This renderer extends the rest_framework's JSONRenderer and adds custom
    handling for User-related data, specifically handling 'ErrorDetail' in the data.

    Attributes:
        charset (str): The character encoding for the response. Default is 'utf-8'.
    """

    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the given data into JSON and handle User-related errors.

        Args:
            data (dict): The data to be rendered.
            accepted_media_type (str, optional): The accepted media type. Default is None.
            renderer_context (dict, optional): The context of the renderer. Default is None.

        Returns:
            str: The JSON-encoded response.

        Note:
            This method overrides the render method of the base JSONRenderer class.
        """

        response = ''

        # Check if 'ErrorDetail' is present in the data
        if 'ErrorDetail' in str(data):
            response = json.dumps({'error': data})
        else:
            response = json.dumps(data)

        return response
