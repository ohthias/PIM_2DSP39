// notas.c
#include <stdio.h>

// Função que calcula média ponderada de NP1 e NP2
double calcular_media(double np1, double np2, double peso_np1, double peso_np2) {
    return np1 * peso_np1 + np2 * peso_np2;
}
