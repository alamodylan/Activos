import qrcode

def generar_codigo_qr(codigo, nombre):
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
    
    # Crear imagen
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"static/{codigo}.png")
    print(f"Código QR generado: {codigo}.png")

# Ejemplo de uso
generar_codigo_qr("ACTIVO000004", "Impresora Bixolon")