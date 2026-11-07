'use strict';
// Generado por python3 server/sync_catalog.py; editar data/catalogo.json.
window.AYLIN_CATALOG = {
  "categories": {
    "deporte": "Ropa deportiva",
    "mascotas": "Mascotas"
  },
  "products": [
    {
      "id": "leggings",
      "name": "Leggings deportivos",
      "category": "deporte",
      "description": "Una propuesta para acompañar tus entrenamientos. Modelo y tallas por confirmar.",
      "alt": "Conjuntos deportivos negros con leggings y zapatillas blancas",
      "priceMinor": 0,
      "stockIsDemo": true,
      "image": "img/shop-leggings.webp",
      "width": 1300,
      "height": 867,
      "author": "MART  PRODUCTION",
      "source": "https://www.pexels.com/photo/legs-of-women-in-sportswear-7894597/",
      "variants": [
        {
          "size": "XS",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "S",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "M",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "L",
          "demoLimit": 20,
          "available": true
        }
      ],
      "sizeGuide": ""
    },
    {
      "id": "top",
      "name": "Top deportivo",
      "category": "deporte",
      "description": "Un básico para tu ropa de entrenamiento. Composición, sujeción y tallas por confirmar.",
      "alt": "Mujer con top deportivo negro en un espacio de entrenamiento",
      "priceMinor": 0,
      "stockIsDemo": true,
      "image": "img/shop-top.webp",
      "width": 967,
      "height": 1450,
      "author": "cottonbro studio",
      "source": "https://www.pexels.com/photo/a-woman-wearing-a-black-activewear-6674232/",
      "variants": [
        {
          "size": "XS",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "S",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "M",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "L",
          "demoLimit": 20,
          "available": true
        }
      ],
      "sizeGuide": ""
    },
    {
      "id": "camiseta",
      "name": "Camiseta deportiva",
      "category": "deporte",
      "description": "Una camiseta para tu rutina activa. Tejido, colores y tallas pendientes de confirmar.",
      "alt": "Camiseta blanca de una persona que sostiene un balón",
      "priceMinor": 0,
      "stockIsDemo": true,
      "image": "img/shop-camiseta.webp",
      "width": 968,
      "height": 1450,
      "author": "ROMAN ODINTSOV",
      "source": "https://www.pexels.com/photo/close-up-photo-of-a-man-holding-a-ball-8084772/",
      "variants": [
        {
          "size": "XS",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "S",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "M",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "L",
          "demoLimit": 20,
          "available": true
        }
      ],
      "sizeGuide": ""
    },
    {
      "id": "correa",
      "name": "Correa para perro",
      "category": "mascotas",
      "description": "Una propuesta para los paseos de cada día. Longitud, material y resistencia por confirmar.",
      "alt": "Perro de pelo largo con correa durante un paseo",
      "priceMinor": 0,
      "stockIsDemo": true,
      "image": "img/shop-correa.webp",
      "width": 967,
      "height": 1450,
      "author": "Paul",
      "source": "https://www.pexels.com/photo/a-dog-on-a-leash-7877091/",
      "variants": [
        {
          "size": "Única",
          "demoLimit": 20,
          "available": true
        }
      ],
      "sizeGuide": ""
    },
    {
      "id": "arnes",
      "name": "Arnés ajustable",
      "category": "mascotas",
      "description": "Una propuesta para pasear en compañía. Ajustes, medidas y compatibilidad por confirmar.",
      "alt": "Perro con arnés azul descansando sobre la hierba",
      "priceMinor": 0,
      "stockIsDemo": true,
      "image": "img/shop-arnes.webp",
      "width": 1087,
      "height": 1450,
      "author": "José Manuel Ramírez Brenis",
      "source": "https://www.pexels.com/photo/blue-french-bulldog-relaxing-outdoors-30243769/",
      "variants": [
        {
          "size": "XS",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "S",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "M",
          "demoLimit": 20,
          "available": true
        },
        {
          "size": "L",
          "demoLimit": 20,
          "available": true
        }
      ],
      "sizeGuide": "Guía provisional: XS, S, M y L. Las medidas definitivas de cuello, pecho y peso deben facilitarlas el fabricante. No selecciones una talla real basándote en esta demo."
    },
    {
      "id": "juguete",
      "name": "Juguete para mascotas",
      "category": "mascotas",
      "description": "Una idea para compartir ratos de juego. Tamaño, materiales y uso recomendado por confirmar.",
      "alt": "Perro sujetando un juguete de cuerda",
      "priceMinor": 0,
      "stockIsDemo": true,
      "image": "img/shop-juguete.webp",
      "width": 1300,
      "height": 867,
      "author": "Filipp Romanovski",
      "source": "https://www.pexels.com/photo/dog-holding-a-rope-in-its-mouth-18478445/",
      "variants": [
        {
          "size": "Única",
          "demoLimit": 20,
          "available": true
        }
      ],
      "sizeGuide": ""
    }
  ]
};
Object.freeze(AYLIN_CATALOG.categories);
AYLIN_CATALOG.products.forEach(p => { p.variants.forEach(Object.freeze); Object.freeze(p.variants); Object.freeze(p); });
Object.freeze(AYLIN_CATALOG.products); Object.freeze(AYLIN_CATALOG);
