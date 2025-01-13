import os

# Obtener variables de entorno
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()

# Comparar si hay espacios en blanco o caracteres adicionales
if aws_access_key_id != os.environ.get("AWS_ACCESS_KEY_ID"):
    print("AWS_ACCESS_KEY_ID tiene espacios en blanco o caracteres adicionales.")
else:
    print("AWS_ACCESS_KEY_ID está limpio.")

if aws_secret_access_key != os.environ.get("AWS_SECRET_ACCESS_KEY"):
    print("AWS_SECRET_ACCESS_KEY tiene espacios en blanco o caracteres adicionales.")
else:
    print("AWS_SECRET_ACCESS_KEY está limpio.")

print(f"AWS_ACCESS_KEY_ID longitud: {len(aws_access_key_id)}")
print(f"AWS_SECRET_ACCESS_KEY longitud: {len(aws_secret_access_key)}")
