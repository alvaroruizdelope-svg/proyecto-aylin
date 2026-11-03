'use strict';

// Cambia solo esta variable cuando dispongas del número definitivo (sin + ni espacios).
const WHATSAPP_NUMBER = '34722892707';
const GENERAL_MESSAGE = 'Hola, he visto la página web de Aylin Nails y me gustaría reservar una cita para hacerme las uñas';

// Contenido editable. Las rutas son relativas a index.html.
const SERVICES = [
  { name: 'Uñas acrílicas', description: 'Forma, longitud y un acabado con personalidad. Una propuesta para expresar tu estilo.', price: 'Consultar precio' },
  { name: 'Extensiones de uñas', description: 'Un extra de longitud para dar forma a ese look que tienes en mente.', price: 'Consultar precio' },
  { name: 'Manicura semipermanente', description: 'Color y un acabado cuidado para acompañarte en tu día a día.', price: 'Consultar precio' },
  { name: 'Diseños y decoración', description: 'Líneas delicadas, pequeños detalles o un toque de color. Tú pones la inspiración.', price: 'Consultar precio' },
  { name: 'Relleno y mantenimiento', description: 'Una puesta a punto para renovar el acabado de tus uñas y seguir cuidándolas.', price: 'Consultar precio' },
  { name: 'Pedicura', description: 'Un momento de cuidado para tus uñas de los pies, con el acabado que más te guste.', price: 'Consultar precio' }
];
// Precios de ejemplo en euros: no son tarifas oficiales. La técnica se propone como inspiración.
const GALLERY = [
  {
    "image": "img/pexels-34997574.webp",
    "title": "Manicura francesa",
    "price": 25,
    "category": "manicura",
    "alt": "Mano con manicura francesa de puntas blancas y anillos dorados",
    "width": 933,
    "height": 1400,
    "author": "Salim Da",
    "source": "https://www.pexels.com/photo/elegant-hand-with-french-manicure-and-jewelry-34997574/"
  },
  {
    "image": "img/pexels-34373400.webp",
    "title": "Manicura efecto perlado",
    "price": 28,
    "category": "manicura",
    "alt": "Uñas cortas de acabado perlado y suave brillo",
    "width": 1050,
    "height": 1400,
    "author": "Moo  Lens",
    "source": "https://www.pexels.com/photo/elegant-manicured-hand-with-gold-rings-34373400/"
  },
  {
    "image": "img/pexels-1839711.webp",
    "title": "Manicura corta lavanda",
    "price": 20,
    "category": "manicura",
    "alt": "Uñas cortas pintadas en tono lavanda junto a un jersey",
    "width": 933,
    "height": 1400,
    "author": "Kristina Paukshtite",
    "source": "https://www.pexels.com/photo/purple-manicure-1839711/"
  },
  {
    "image": "img/pexels-10944916.webp",
    "title": "Manicura en violeta",
    "price": 23,
    "category": "manicura",
    "alt": "Manos con uñas de color violeta y un anillo",
    "width": 1200,
    "height": 800,
    "author": "MiM Fathi",
    "source": "https://www.pexels.com/photo/a-close-up-shot-of-a-woman-wearing-a-gold-ring-10944916/"
  },
  {
    "image": "img/pexels-17010955.webp",
    "title": "Acrílicas rojas almendradas",
    "price": 42,
    "category": "acrilicas",
    "alt": "Uñas largas almendradas de color rojo",
    "width": 1120,
    "height": 1400,
    "author": "Andrea Mosti",
    "source": "https://www.pexels.com/photo/fingers-decorated-with-red-acrylic-nails-17010955/"
  },
  {
    "image": "img/pexels-15491630.webp",
    "title": "Acrílicas con corazones",
    "price": 48,
    "category": "acrilicas",
    "alt": "Uñas acrílicas con base nude y corazones rojos",
    "width": 1050,
    "height": 1400,
    "author": "Linda Markaj",
    "source": "https://www.pexels.com/photo/close-up-of-acrylic-nails-decorated-with-heart-shapes-15491630/"
  },
  {
    "image": "img/pexels-28712961.webp",
    "title": "Acrílicas con brillo",
    "price": 55,
    "category": "acrilicas",
    "alt": "Uñas largas con detalles de purpurina y acabado rosa",
    "width": 1120,
    "height": 1400,
    "author": "Sebastian Balog",
    "source": "https://www.pexels.com/photo/elegant-nail-art-with-glitter-accent-on-hands-28712961/"
  },
  {
    "image": "img/pexels-6135680.webp",
    "title": "Extensiones acrílicas",
    "price": 40,
    "category": "acrilicas",
    "alt": "Aplicación de una extensión acrílica durante una manicura",
    "width": 1200,
    "height": 800,
    "author": "Gabriel Puyén",
    "source": "https://www.pexels.com/photo/woman-getting-acrylic-nails-6135680/"
  },
  {
    "image": "img/pexels-3557600.webp",
    "title": "Decoración de lunares",
    "price": 30,
    "category": "disenos",
    "alt": "Manicura clara con pequeños puntos sobre un jersey de punto",
    "width": 933,
    "height": 1400,
    "author": "Kristina Paukshtite",
    "source": "https://www.pexels.com/photo/photo-of-person-s-hand-3557600/"
  },
  {
    "image": "img/pexels-4965824.webp",
    "title": "Diseño geométrico",
    "price": 35,
    "category": "disenos",
    "alt": "Uñas con decoración geométrica sobre fondo amarillo y negro",
    "width": 1200,
    "height": 800,
    "author": "cottonbro studio",
    "source": "https://www.pexels.com/photo/persons-hand-on-yellow-and-black-textile-4965824/"
  },
  {
    "image": "img/pexels-10632142.webp",
    "title": "Diseño dorado de fiesta",
    "price": 38,
    "category": "disenos",
    "alt": "Manicura con purpurina dorada junto a estrellas decorativas",
    "width": 1200,
    "height": 900,
    "author": "Pexels User",
    "source": "https://www.pexels.com/photo/person-s-hands-with-gold-glitter-nails-10632142/"
  },
  {
    "image": "img/pexels-17056222.webp",
    "title": "Pedicura clásica",
    "price": 25,
    "category": "pedicura",
    "alt": "Aplicación de esmalte en las uñas de los pies con guantes protectores",
    "width": 933,
    "height": 1400,
    "author": "Andrea Mosti",
    "source": "https://www.pexels.com/photo/close-up-of-woman-doing-pedicure-17056222/"
  },
  {
    "image": "img/pexels-5484947.webp",
    "title": "Pedicura con color",
    "price": 30,
    "category": "pedicura",
    "alt": "Pedicura con esmalte naranja durante su aplicación",
    "width": 1200,
    "height": 800,
    "author": "Felix Adams",
    "source": "https://www.pexels.com/photo/person-getting-her-nails-done-5484947/"
  },
  {
    "image": "img/pexels-4963822.webp",
    "title": "Pedicura verde suave",
    "price": 18,
    "category": "pedicura",
    "alt": "Uñas de los pies pintadas en un tono verde claro",
    "width": 933,
    "height": 1400,
    "author": "https://kaboompics.com/",
    "source": "https://www.pexels.com/photo/close-up-view-of-toes-on-carpet-4963822/"
  }
];
const NEWS = [
  { title: 'La belleza de lo natural', date: '2026-10-12', label: 'INSPIRACIÓN · DEMO', image: 'img/pexels-3557600.webp', alt: 'Fotografía de manicura en tonos suaves con pequeños lunares', description: 'Tonos suaves, formas delicadas y ese acabado que combina con todo.', content: 'Los tonos nude y rosa empolvado son el punto de partida de este moodboard. Guarda tu referencia favorita y coméntala al consultar tu cita. Publicación ficticia de ejemplo; no muestra un servicio ya realizado.' },
  { title: 'Pequeños detalles, mucho estilo', date: '2026-10-19', label: 'DISEÑOS · DEMO', image: 'img/pexels-15491630.webp', alt: 'Fotografía de uñas nude decoradas con corazones rojos', description: 'Una línea, un motivo, un color inesperado. Inspírate para tu próximo diseño.', content: 'Una decoración puede ser tan sutil o tan expresiva como quieras. Esta fotografía de inspiración explora pequeños motivos sobre una base suave. Las opciones reales y su disponibilidad se confirmarán con Aylin.' },
  { title: 'Tu próximo momento de cuidado', date: '2026-10-26', label: 'AVISO · DEMO', image: 'img/pexels-4963822.webp', alt: 'Fotografía de pedicura con esmalte verde suave', description: 'Este será el espacio para compartir avisos, nuevos servicios y futuras promociones.', content: 'Ejemplo de publicación: aquí se podrán anunciar promociones con sus fechas, condiciones y precios confirmados. Actualmente no hay ninguna oferta activa ni una promoción comercial real.' }
];

function whatsappUrl(service) {
  const message = service
    ? `Hola, he visto la página web de Aylin Nails y me gustaría reservar una cita para ${service.toLocaleLowerCase('es')}`
    : GENERAL_MESSAGE;
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
}
function configureBookingLink(link, service) {
  link.href = whatsappUrl(service);
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.setAttribute('aria-label', `${service ? `Reservar ${service}` : 'Reservar cita'} por WhatsApp (número de prueba, abre otra pestaña)`);
}
document.querySelectorAll('[data-reserva]').forEach(link => configureBookingLink(link));

const nailIcon = '<svg viewBox="0 0 48 56" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true"><path d="M15 45V20c0-16 18-16 18 0v25c0 10-18 10-18 0Z"/><path d="M15 26c6 4 12 4 18 0M21 14c0-5 5-5 5-5M5 11h7M8.5 7.5v7M36 41h7M39.5 37.5v7"/></svg>';
const servicesList = document.querySelector('#servicios-lista');
SERVICES.forEach((service, index) => {
  const card = document.createElement('article');
  card.className = 'service-card reveal';
  card.innerHTML = `<div class="service-top">${nailIcon}<span>0${index + 1}</span></div><h3></h3><p></p><div class="service-bottom"><span class="price"></span><a>Reservar ↗</a></div>`;
  card.querySelector('h3').textContent = service.name;
  card.querySelector('p').textContent = service.description;
  card.querySelector('.price').textContent = service.price;
  configureBookingLink(card.querySelector('a'), service.name);
  servicesList.append(card);
});

let currentFilter = 'todas';
let activeIndex = 0;
let previousFocus;
const lightbox = document.querySelector('#lightbox');
const lightboxImage = document.querySelector('#lightbox-img');
const galleryList = document.querySelector('#galeria-lista');
const filteredGallery = () => GALLERY.filter(item => currentFilter === 'todas' || item.category === currentFilter);
const euroPrice = value => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value);
function showImage(index) {
  const items = filteredGallery();
  activeIndex = (index + items.length) % items.length;
  const item = items[activeIndex];
  lightboxImage.src = item.image;
  lightboxImage.alt = item.alt;
  document.querySelector('#lightbox-caption').textContent = item.title;
  document.querySelector('#lightbox-price').textContent = `${euroPrice(item.price)} · precio orientativo provisional`;
  document.querySelector('#lightbox-position').textContent = `${activeIndex + 1} / ${items.length}`;
  const credit = document.querySelector('#lightbox-credit');
  credit.textContent = `Foto: ${item.author} / Pexels`;
  credit.href = item.source;
  configureBookingLink(document.querySelector('#lightbox-booking'), item.title);
}
GALLERY.forEach(item => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'gallery-item reveal';
  button.dataset.category = item.category;
  button.setAttribute('aria-label', `Ampliar ${item.title}, ${euroPrice(item.price)}, precio orientativo provisional, fotografía de inspiración`);
  const img = document.createElement('img');
  img.src = item.image;
  img.alt = item.alt;
  img.loading = 'lazy';
  img.width = item.width;
  img.height = item.height;
  const caption = document.createElement('span');
  caption.className = 'gallery-caption';
  const title = document.createElement('span');
  const name = document.createElement('span');
  name.textContent = item.title;
  const price = document.createElement('small');
  price.textContent = `${euroPrice(item.price)} · orientativo`;
  title.append(name, price);
  const plus = document.createElement('span');
  plus.textContent = '+';
  plus.setAttribute('aria-hidden', 'true');
  caption.append(title, plus);
  button.append(img, caption);
  button.addEventListener('click', () => {
    previousFocus = button;
    showImage(filteredGallery().indexOf(item));
    lightbox.showModal();
    document.body.classList.add('modal-open');
  });
  galleryList.append(button);
});
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  currentFilter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(filter => {
    const selected = filter === button;
    filter.classList.toggle('active', selected);
    filter.setAttribute('aria-pressed', String(selected));
  });
  galleryList.querySelectorAll('.gallery-item').forEach(item => {
    item.hidden = currentFilter !== 'todas' && item.dataset.category !== currentFilter;
  });
  document.querySelector('#gallery-status').textContent = `${filteredGallery().length} fotografías en ${button.textContent}`;
}));
document.querySelector('#lightbox-close').addEventListener('click', () => lightbox.close());
document.querySelector('#lightbox-prev').addEventListener('click', () => showImage(activeIndex - 1));
document.querySelector('#lightbox-next').addEventListener('click', () => showImage(activeIndex + 1));
lightbox.addEventListener('close', () => {
  document.body.classList.remove('modal-open');
  previousFocus?.focus();
});
lightbox.addEventListener('click', event => {
  const rect = lightbox.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) lightbox.close();
});
lightbox.addEventListener('keydown', event => {
  if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
    event.preventDefault();
    showImage(activeIndex + (event.key === 'ArrowRight' ? 1 : -1));
  }
});
let touchStartX = 0;
let touchStartY = 0;
lightboxImage.addEventListener('touchstart', event => {
  touchStartX = event.changedTouches[0].clientX;
  touchStartY = event.changedTouches[0].clientY;
}, { passive: true });
lightboxImage.addEventListener('touchend', event => {
  const dx = event.changedTouches[0].clientX - touchStartX;
  const dy = event.changedTouches[0].clientY - touchStartY;
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) showImage(activeIndex + (dx < 0 ? 1 : -1));
}, { passive: true });

NEWS.forEach(post => {
  const article = document.createElement('article');
  article.className = 'news-card reveal';
  const image = document.createElement('img');
  image.src = post.image;
  image.alt = post.alt;
  image.loading = 'lazy';
  const photo = GALLERY.find(item => item.image === post.image);
  image.width = photo?.width || 800;
  image.height = photo?.height || 500;
  const copy = document.createElement('div');
  copy.className = 'news-copy';
  const meta = document.createElement('div');
  meta.className = 'news-meta';
  const date = document.createElement('time');
  date.dateTime = post.date;
  date.textContent = new Intl.DateTimeFormat('es', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${post.date}T12:00:00Z`));
  meta.append(`${post.label} · Fecha de ejemplo: `, date);
  const title = document.createElement('h3');
  title.textContent = post.title;
  const description = document.createElement('p');
  description.textContent = post.description;
  copy.append(meta, title, description);
  if (post.content) {
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Leer más';
    summary.setAttribute('aria-label', `Leer más: ${post.title}`);
    const content = document.createElement('p');
    content.textContent = post.content;
    details.append(summary, content);
    details.addEventListener('toggle', () => { summary.textContent = details.open ? 'Leer menos' : 'Leer más'; });
    copy.append(details);
  }
  if (photo) {
    const credit = document.createElement('p');
    credit.className = 'news-photo-credit';
    const link = document.createElement('a');
    link.href = photo.source;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = `Foto: ${photo.author} / Pexels`;
    credit.append(link);
    copy.append(credit);
  }
  article.append(image, copy);
  document.querySelector('#novedades-lista').append(article);
});

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#navegacion');
function closeMenu(returnFocus = false) {
  navigation.classList.remove('open');
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', 'Abrir menú');
  if (returnFocus) menuButton.focus();
}
menuButton.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  navigation.classList.toggle('open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
});
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => closeMenu()));
document.addEventListener('keydown', event => { if (event.key === 'Escape' && navigation.classList.contains('open')) closeMenu(true); });
document.addEventListener('click', event => { if (!event.target.closest('.header')) closeMenu(); });
const mobileQuery = window.matchMedia('(max-width: 800px)');
mobileQuery.addEventListener('change', () => closeMenu());
document.querySelector('#year').textContent = new Date().getFullYear();
if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.remove('pending');
      observer.unobserve(entry.target);
    }
  }), { threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(element => {
    element.classList.add('pending');
    observer.observe(element);
  });
}

// Créditos visibles y enlaces a las páginas originales, sin dependencias externas de carga.
GALLERY.forEach(item => {
  const row = document.createElement('li');
  const link = document.createElement('a');
  link.href = item.source;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.textContent = `${item.title} — ${item.author} / Pexels`;
  row.append(link);
  document.querySelector('#photo-credit-list').append(row);
});
