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
const GALLERY = [
  { image: 'img/nude.svg', title: 'The nude edit', category: 'acrilicas', alt: 'Ilustración de uñas acrílicas almendradas en rosa nude' },
  { image: 'img/francesa.svg', title: 'Siempre francesa', category: 'manicura', alt: 'Ilustración de manicura francesa con puntas blancas' },
  { image: 'img/cereza.svg', title: 'Un toque de cereza', category: 'disenos', alt: 'Ilustración de uñas con pequeños motivos de cerezas' },
  { image: 'img/burdeos.svg', title: 'Rojo, sin más', category: 'acrilicas', alt: 'Ilustración de uñas largas en color burdeos' },
  { image: 'img/dorado.svg', title: 'Luz en los detalles', category: 'disenos', alt: 'Ilustración de uñas nude con líneas doradas' },
  { image: 'img/pedicura.svg', title: 'Pies en calma', category: 'pedicura', alt: 'Ilustración de muestras de esmalte rosa para pedicura' }
];
const NEWS = [
  { title: 'La belleza de lo natural', date: '2026-10-12', label: 'INSPIRACIÓN · DEMO', image: 'img/nude.svg', alt: 'Ilustración de uñas nude', description: 'Tonos suaves, formas delicadas y ese acabado que combina con todo.', content: 'Los tonos nude y rosa empolvado son el punto de partida de este moodboard. Guarda tu referencia favorita y coméntala al consultar tu cita. Publicación ficticia de ejemplo; no muestra un servicio ya realizado.' },
  { title: 'Pequeños detalles, mucho estilo', date: '2026-10-19', label: 'DISEÑOS · DEMO', image: 'img/cereza.svg', alt: 'Ilustración de decoración de uñas con cerezas', description: 'Una línea, un motivo, un color inesperado. Inspírate para tu próximo diseño.', content: 'Una decoración puede ser tan sutil o tan expresiva como quieras. Esta propuesta ilustrada explora pequeños motivos sobre una base suave. Las opciones reales y su disponibilidad se confirmarán con Aylin.' },
  { title: 'Tu próximo momento de cuidado', date: '2026-10-26', label: 'AVISO · DEMO', image: 'img/estudio.svg', alt: 'Ilustración de esmaltes para uñas', description: 'Este será el espacio para compartir avisos, nuevos servicios y futuras promociones.', content: 'Ejemplo de publicación: aquí se podrán anunciar promociones con sus fechas, condiciones y precios confirmados. Actualmente no hay ninguna oferta activa ni una promoción comercial real.' }
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
function showImage(index) {
  const items = filteredGallery();
  activeIndex = (index + items.length) % items.length;
  const item = items[activeIndex];
  lightboxImage.src = item.image;
  lightboxImage.alt = item.alt;
  document.querySelector('#lightbox-caption').textContent = `${item.title} · ${activeIndex + 1} / ${items.length}`;
}
GALLERY.forEach(item => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'gallery-item reveal';
  button.dataset.category = item.category;
  button.setAttribute('aria-label', `Ampliar ${item.title}, ilustración de demostración`);
  const img = document.createElement('img');
  img.src = item.image;
  img.alt = item.alt;
  img.loading = 'lazy';
  img.width = 800;
  img.height = 1000;
  const caption = document.createElement('span');
  caption.className = 'gallery-caption';
  const title = document.createElement('span');
  title.textContent = item.title;
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
  document.querySelector('#gallery-status').textContent = `${filteredGallery().length} ilustraciones en ${button.textContent}`;
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
  image.width = 800;
  image.height = 500;
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
