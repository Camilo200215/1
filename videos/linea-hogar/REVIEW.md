# REVIEW — "Todo empieza con una línea" (15 s, 1920x1080, 30 fps)

- Decisiones creativas: tema libre → una línea de tinta que se vuelve plano, maqueta 3D (CSS 3D real con cámara que se inclina y orbita), muebles que caen, anochecer y lámpara que enciende el hogar. Look de maqueta de arquitecto en cartón pluma con aristas entintadas; un solo acento (la luz).
- Medido: `hyperframes check` ok; revisé snapshots en 0, 1.4, 4, 7, 9, 10.5, 13, 14.8 s y fotogramas del MP4 final.
- Sin sonido: no hay sesión de HeyGen para el catálogo de música. Para añadirla: `npx hyperframes auth login`, y luego música + whoosh en la inclinación y un golpe al encender la lámpara (10 s).
- Advertencias mantenidas: contraste de "hogar." en amarillo sobre el fondo de noche (~2.4–3:1, texto grande y es el acento a propósito); 5 títulos en una pista (cosmético).
- Plano más débil: 0–3 s es solo línea + texto; con más tiempo, un lápiz o una punta visible dibujando la línea.
- GSAP se sirve desde `assets/gsap.min.js` porque el navegador del render no alcanza el CDN en este entorno.
