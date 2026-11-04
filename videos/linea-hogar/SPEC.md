# SPEC — "Todo empieza con una línea"

GOAL:    el espectador ve cómo una sola línea de tinta se vuelve un hogar encendido, y se queda con "Diseña lo que vives."
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    15 s x 30 = 450 frames. Sin música en esta versión (sin sesión de HeyGen).
LOOK:    medio = maqueta de arquitecto en cartón pluma, cada arista entintada.
         ground #C9CEC0 (salvia gris) liso + ruido de fibra 5 %; ink #1C1C1A; cartón #F5F3EE / #E6E2D8 / #D6D1C5;
         madera melamina #B5835A / #D3A878; tela #46534C; acento #FFB31A SOLO en la luz de la lámpara y la palabra "hogar".
         Display Outfit 700, 84 px (7.8 % alto), tracking -2 %; frase final 128 px.
         Aristas: 3 px tinta en muros, 2 px en muebles. Sombra de contacto de la base: 0 40px 60px rgba(0,0,0,.25).
OBJECTS: plano de planta (muro exterior + 2 muros interiores con vanos de puerta), sofá, mesa de centro, mueble TV,
         lámpara de pie (poste + pantalla), cama con cabecero, mesa de comedor. Todos cajas 3D con 5 caras.
MOTION:  llegada expo.out / power4.out; cámara power2.inOut; muebles caen con back.out(1.6) (≈ damping 0.6);
         títulos dead still al aterrizar; salidas blur 8 px en 0.2 s.
SHOTS:   f0–90    la línea se dibuja de izq. a der. (1.3 s, power3.inOut); "Todo empieza con una línea." palabra a palabra con blur.
         f90–190  la línea cierra el plano: muros y tabiques se dibujan, aparece el cartón; "Una línea se vuelve plano." gris→tinta.
         f130–200 la cámara se inclina de cenital a isométrica (2 s).
         f185–280 los muros se extruyen hacia arriba, caen los muebles uno a uno; "Un plano se vuelve espacio." línea entera con blur.
         f282–300 anochece (colour flood del fondo y velo multiplicado 0.5 s).
         f300     golpe: se enciende la lámpara (tl.set), charco de luz crece 0.6 s; "Y un espacio, un hogar." "hogar" en acento.
         f318–450 órbita lenta de cámara (≈ 3°/s) y alejamiento; f370 "Diseña lo que vives." letra a letra, se sostiene 2.6 s.
BANNED:  vacío negro/navy con cosas flotando; glow/neón/partículas; gradientes morados; tarjetas de vidrio;
         papel crema + serif + etiquetas mono; todo centrado; todo entrando con fade+slide-up; títulos que se mueven al leerse;
         logo en esquina; respiración/pulsos en bucle.
QA:      t=1.4 (línea a medio dibujar), 4.0 (plano completo), 7.0 (muros subiendo), 9.0 (muebles), 10.4 (lámpara encendida), 14.5 (final).
