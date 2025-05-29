import random

def generar_codigo_otp():
    return str(random.randint(100000, 999999))  # Código de 6 dígitos
