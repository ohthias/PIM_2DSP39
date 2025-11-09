import ctypes
import os

# Caminho da biblioteca
LIB_PATH = os.path.join(os.path.dirname(__file__), "../libs", "notas.dll")  # ou .dll no Windows

# Carrega a biblioteca
lib = ctypes.CDLL(LIB_PATH)

# Define tipos de entrada e saída da função
lib.calcular_media.restype = ctypes.c_double
lib.calcular_media.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]

def calcular_media_c(np1, np2, peso_np1=0.4, peso_np2=0.6):
    return lib.calcular_media(np1, np2, peso_np1, peso_np2)
