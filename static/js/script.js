const navbar = document.getElementById('navbar');
const mobileBtn = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');
const overlay = document.getElementById('overlay');
let menuOpen = false;

// Navbar scroll effect
function handleScroll() {
  if (window.scrollY > 50) {
    navbar.classList.add('bg-[#06038D]/80');
  } else {
    navbar.classList.remove('bg-[#06038D]/80');
  }
}
handleScroll();
window.addEventListener('scroll', handleScroll);
window.addEventListener('resize', handleScroll);

// Mobile menu toggle
mobileBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  menuOpen = !menuOpen;
  mobileMenu.style.right = menuOpen ? '0' : '-70%';
  overlay.classList.toggle('hidden', !menuOpen);
});

document.addEventListener('click', (e) => {
  if (menuOpen && !mobileMenu.contains(e.target) && !mobileBtn.contains(e.target)) {
    closeMenu();
  }
});

overlay.addEventListener('click', closeMenu);
function closeMenu() {
  menuOpen = false;
  mobileMenu.style.right = '-70%';
  overlay.classList.add('hidden');
}

// === Language Toggles (Sync Desktop & Mobile) ===
const langToggle = document.getElementById('lang-toggle');
const langLabel = document.getElementById('lang-label');
const mobileLangToggle = document.getElementById('mobile-lang-toggle');
const mobileLangLabel = document.getElementById('mobile-lang-label');

function updateLanguageUI(isEnglish) {
  langLabel.textContent = isEnglish ? 'ENG' : 'TAMIL';
  mobileLangLabel.textContent = isEnglish ? 'ENG' : 'TAMIL';
  langToggle.checked = isEnglish;
  mobileLangToggle.checked = isEnglish;
}

// Desktop toggle
langToggle.addEventListener('change', () => {
  updateLanguageUI(langToggle.checked);
});

// Mobile toggle
mobileLangToggle.addEventListener('change', () => {
  updateLanguageUI(mobileLangToggle.checked);
});

// Default: Tamil
updateLanguageUI(false);


const slides = document.querySelectorAll('.slide');
const boxes = document.querySelectorAll('.slide-box');
const prevBtn = document.getElementById('prev-slide');
const nextBtn = document.getElementById('next-slide');

let current = 0;
let autoSlide;

// Show slide function
function showSlide(i) {
  slides.forEach((slide, idx) => {
    slide.style.opacity = idx === i ? '1' : '0';
    slide.style.transition = 'opacity 1s ease-in-out';
  });

  boxes.forEach(box => box.classList.toggle('hidden', box.dataset.slide != i));
}

// Next slide
function nextSlide() {
  current = (current + 1) % slides.length;
  showSlide(current);
}

// Previous slide
function prevSlideFunc() {
  current = (current - 1 + slides.length) % slides.length;
  showSlide(current);
}

// Auto slide
function startAutoSlide() {
  autoSlide = setInterval(nextSlide, 4000);
}

// Stop auto slide
function stopAutoSlide() {
  clearInterval(autoSlide);
}

// Initial display
showSlide(current);
startAutoSlide();

// Arrow navigation
nextBtn.addEventListener('click', () => {
  stopAutoSlide();
  nextSlide();
  startAutoSlide();
});

prevBtn.addEventListener('click', () => {
  stopAutoSlide();
  prevSlideFunc();
  startAutoSlide();
});

// Mouse wheel navigation
let isScrolling = false;
window.addEventListener('wheel', (e) => {
  if (isScrolling) return;
  isScrolling = true;

  stopAutoSlide();

  if (e.deltaY > 0) nextSlide();
  else prevSlideFunc();

  startAutoSlide();

  setTimeout(() => isScrolling = false, 800);
});

// Touch swipe for mobile
let startX = 0;
let endX = 0;

window.addEventListener('touchstart', (e) => {
  startX = e.touches[0].clientX;
  stopAutoSlide();
});

window.addEventListener('touchmove', (e) => {
  endX = e.touches[0].clientX;
});

window.addEventListener('touchend', () => {
  const deltaX = endX - startX;
  if (Math.abs(deltaX) > 50) {
    if (deltaX < 0) nextSlide(); // swipe left → next
    else prevSlideFunc();         // swipe right → prev
  }
  startAutoSlide();
});



