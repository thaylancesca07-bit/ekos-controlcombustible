import numpy as np

def concatenar_matrizes(matriz_A, matriz_B, modo='vertical'):
    """
    Concatena dos matrices (A y B).
    
    Parámetros:
    - matriz_A, matriz_B: Listas de listas o arrays de Numpy.
    - modo: 'vertical' (agrega filas abajo) o 'horizontal' (agrega columnas al lado).
    
    Retorna:
    - Nueva matriz concatenada o mensaje de error si las dimensiones no coinciden.
    """
    
    # Convertimos a arrays de numpy para facilitar la manipulación
    arr_A = np.array(matriz_A)
    arr_B = np.array(matriz_B)
    
    try:
        if modo == 'vertical':
            # axis=0 concatena a lo largo de las filas (verticalmente)
            # A y B deben tener el mismo número de COLUMNAS
            resultado = np.concatenate((arr_A, arr_B), axis=0)
            
        elif modo == 'horizontal':
            # axis=1 concatena a lo largo de las columnas (horizontalmente)
            # A y B deben tener el mismo número de FILAS
            resultado = np.concatenate((arr_A, arr_B), axis=1)
            
        else:
            return "Error: El modo debe ser 'vertical' o 'horizontal'."
            
        return resultado

    except ValueError as e:
        return f"Error de dimensión: {e}. Verifica que las matrices coincidan en tamaño para la operación deseada."

# --- Bloque de Prueba (Main) ---
if __name__ == "__main__":
    # Definición de matrices de ejemplo (2x3)
    A = [
        [1, 2, 3],
        [4, 5, 6]
    ]
    
    B = [
        [7, 8, 9],
        [10, 11, 12]
    ]

    print("--- Matriz A ---")
    print(np.array(A))
    print("\n--- Matriz B ---")
    print(np.array(B))

    # 1. Prueba Vertical (Una debajo de la otra)
    print("\n--- Resultado Concatenación Vertical ---")
    res_v = concatenar_matrizes(A, B, modo='vertical')
    print(res_v)

    # 2. Prueba Horizontal (Una al lado de la otra)
    print("\n--- Resultado Concatenación Horizontal ---")
    res_h = concatenar_matrizes(A, B, modo='horizontal')
    print(res_h)
