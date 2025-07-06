import random
import string

def generar_codigo_otp():
    return str(random.randint(100000, 999999))  # Código de 6 dígitos

def generar_password_temporal():
    """Genera una contraseña temporal de 8 caracteres alfanuméricos"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(8))

def enviar_email_activacion(usuario, password_temporal):
    """Envía email de activación con contraseña temporal"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.urls import reverse
    
    # URL de activación
    activation_url = f"{settings.SITE_URL}/usuarios/activar/{usuario.activation_token}/"
    
    subject = 'Activación de cuenta - Sistema de Alquiler de Autos'
    message = f"""
    Hola {usuario.nombre} {usuario.apellido},
    
    Tu cuenta ha sido creada por nuestro personal. Para activarla, sigue estos pasos:
    
    1. Haz clic en el siguiente enlace para activar tu cuenta:
    {activation_url}
    
    2. Usa esta contraseña temporal para iniciar sesión:
    Usuario: {usuario.username}
    Contraseña temporal: {password_temporal}
    
    3. Una vez que inicies sesión, podrás cambiar tu contraseña.
    
    IMPORTANTE: Esta contraseña es temporal y debes cambiarla en tu primer inicio de sesión.
    
    Si no solicitaste esta cuenta, puedes ignorar este email.
    
    Saludos,
    Equipo de Alquiler de Autos
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [usuario.correo],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False
