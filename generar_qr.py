import qrcode
import os

# Crear la carpeta 'qr-codes' si no existe
if not os.path.exists("static/qr-codes"):
    os.makedirs("static/qr-codes")

def generar_codigo_qr(codigo, nombre):
    # Contenido del código QR
    contenido = f"ID: {codigo}\nNombre: {nombre}"
    
    # Generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(contenido)
    qr.make(fit=True)
    
    # Guardar la imagen en la carpeta 'static/qr-codes'
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"static/qr-codes/{codigo}.png")
    print(f"Código QR generado: static/qr-codes/{codigo}.png")