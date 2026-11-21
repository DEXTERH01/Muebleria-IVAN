# Protocolo de evaluación con usuarios

## Objetivo

Evaluar si personas que no desarrollaron Mueblería Iván pueden encontrar un producto, preparar una cotización y entender el seguimiento de un pedido. La sesión identifica problemas de uso; no mide la calidad comercial de los precios ni la precisión de los modelos.

## Participantes y duración

- Invitar de 5 a 8 personas adultas que no hayan participado en el desarrollo.
- Incluir visitantes/clientes potenciales y, si están disponibles, personas con experiencia de operación o administración.
- Duración por sesión: 20 a 25 minutos.
- Usar una cuenta y datos de demostración separados de cualquier dato operativo.

## Preparación

1. Confirmar que la demo esté desplegada y que Auth funcione con una cuenta de prueba.
2. Preparar un navegador actualizado y una pantalla móvil de 360–390 px; alternar con una pantalla de escritorio.
3. Limpiar datos de sesión antes de cada participante.
4. Asignar un código anónimo (`P01`…`P08`); no registrar nombre, correo, teléfono, contraseña ni audio/video identificable.
5. Explicar el objetivo, que se evalúa el prototipo y no a la persona, y pedir consentimiento antes de iniciar.
6. No crear pagos reales ni cambiar configuración fuera de los datos de demo.

## Guion de tareas

El moderador lee cada situación sin indicar dónde pulsar. Registra éxito, tiempo, errores y observaciones con el código anónimo.

| N.º | Situación | Éxito observable |
| --- | --- | --- |
| 1 | Encuentra un mueble apropiado para un dormitorio y revisa sus detalles. | Abre un producto y reconoce su precio de referencia. |
| 2 | Configura ese mueble con medidas, material y acabado; solicita una cotización. | Envía el formulario y localiza el total y el código de cotización. |
| 3 | Comparte los datos de la cotización usando el mensaje preparado. | Abre el mensaje, lo copia y puede volver al resumen. |
| 4 | Inicia sesión con la cuenta de demostración y busca sus proyectos. | Accede al portal y reconoce cotizaciones, etapas y saldo. |
| 5 | (Solo rol operador/admin) Revisa una cotización de prueba y avanza su estado. | Cambia el estado una vez y distingue la recomendación de una acción automática. |

Si la configuración de Auth o el rol de demostración no está disponible, marcar las tareas 4 y 5 como **no ejecutadas por bloqueo técnico**; no contarlas como fallidas por uso.

## Registro por tarea

| Participante | Tarea | Completada (sí/parcial/no) | Tiempo (s) | Errores / retrocesos | Ayuda del moderador | Nota anónima |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

- Un error es una acción que no acerca al objetivo o que obliga a corregir información.
- Detener una sesión si la persona lo solicita o si la demo muestra información real.
- No sugerir la respuesta. Si hay bloqueo por más de 60 segundos, registrar el bloqueo y ofrecer ayuda para continuar.

## Cuestionario SUS

Al terminar, pedir una puntuación de 1 (totalmente en desacuerdo) a 5 (totalmente de acuerdo):

1. Me gustaría usar este sistema con frecuencia.
2. Encontré el sistema innecesariamente complicado.
3. El sistema me pareció fácil de usar.
4. Creo que necesitaría ayuda técnica para usar este sistema.
5. Las funciones del sistema me parecieron bien integradas.
6. Encontré demasiadas inconsistencias en el sistema.
7. Imagino que la mayoría de personas aprendería a usarlo rápidamente.
8. El sistema me pareció difícil de usar.
9. Me sentí seguro/a usando el sistema.
10. Necesité aprender muchas cosas antes de poder usarlo.

Calcular por participante: sumar `respuesta - 1` para los ítems impares y `5 - respuesta` para los pares; multiplicar el total por 2.5. Reportar los puntajes individuales anonimizados, la media y el número de respuestas. No describir la media como aprobación universal.

## Resumen de resultados

Completar solo después de las sesiones reales:

- Participantes completados: ___ / 5–8
- Tasa de éxito por tarea: tareas completadas / tareas intentadas, excluyendo las marcadas como bloqueadas técnicamente.
- Mediana del tiempo por tarea: ___ s
- Errores más frecuentes: ___
- SUS individual (P01…): ___
- SUS promedio: ___ / 100
- Problemas priorizados (impacto, frecuencia, pantalla, corrección): ___

No ingresar resultados previstos ni datos de sesiones simuladas en este resumen.
