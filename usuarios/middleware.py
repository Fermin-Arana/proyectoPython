from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que no requieren cambio de contraseña
        exempt_urls = [
            reverse('cambiar_password_inicial'),
            reverse('logout'),
            '/admin/',
        ]
        
        if (request.user.is_authenticated and 
            request.user.created_by_employee and 
            request.path not in exempt_urls and 
            not request.path.startswith('/static/')):
            
            messages.warning(request, "Debes cambiar tu contraseña temporal antes de continuar.")
            return redirect('cambiar_password_inicial')
        
        response = self.get_response(request)
        return response