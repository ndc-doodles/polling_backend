document.addEventListener('DOMContentLoaded', () => {
  const mobileBtn = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  const overlay = document.getElementById('overlay');
  let menuOpen = false;

  // === Mobile Sidebar Toggle ===
  mobileBtn.addEventListener('click', () => {
    menuOpen = !menuOpen;
    mobileMenu.style.right = menuOpen ? '0' : '-70%';
    overlay.classList.toggle('hidden', !menuOpen);
  });

  overlay.addEventListener('click', () => {
    menuOpen = false;
    mobileMenu.style.right = '-70%';
    overlay.classList.add('hidden');
  });

  // === Language Toggles (Desktop & Mobile) ===
  const langToggle = document.getElementById('lang-toggle');
  const langLabel = document.getElementById('lang-label');
  const mobileLangToggle = document.getElementById('mobile-lang-toggle');
  const mobileLangLabel = document.getElementById('mobile-lang-label');

  // Sync UI updates
  function updateLanguage(isEnglish) {
    langLabel.textContent = isEnglish ? 'ENG' : 'TAMIL';
    mobileLangLabel.textContent = isEnglish ? 'ENG' : 'TAMIL';
    langToggle.checked = isEnglish;
    mobileLangToggle.checked = isEnglish;
  }

  // === Event Listeners ===
  langToggle.addEventListener('change', () => {
    updateLanguage(langToggle.checked);
  });

  mobileLangToggle.addEventListener('change', () => {
    updateLanguage(mobileLangToggle.checked);
  });

  // === Default Language: Tamil (gray switch) ===
  updateLanguage(false);
});














(function () {
  // === Toggle share popup visibility ===
  document.querySelectorAll('.share-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const popup = btn.nextElementSibling;

      // Close other popups
      document.querySelectorAll('.share-popup').forEach(p => {
        if (p !== popup) p.classList.add('hidden');
      });

      popup.classList.toggle('hidden');
    });
  });

  // === Close all popups on outside click ===
  document.addEventListener('click', () => {
    document.querySelectorAll('.share-popup').forEach(p => p.classList.add('hidden'));
  });

  // === Platform-specific sharing (with bold heading, paragraph, and read more link) ===
  document.querySelectorAll('.share-popup button[data-platform]').forEach(opt => {
    opt.addEventListener('click', e => {
      e.stopPropagation();

      const container = opt.closest('.news-card');
      const title = container?.dataset.title || 'Latest News';
      const description = container?.dataset.description?.slice(0, 120) || '';
      const detailPage = `${window.location.origin}/polling/blog_detail.html`;

      // Message structure for sharing — bold title + description + link
      const message = `**${title}**\n\n${description}...\n\nRead more: ${detailPage}`;
      const encodedMessage = encodeURIComponent(message);

      let shareUrl = '';

      switch (opt.dataset.platform) {
        case 'facebook':
          shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(detailPage)}&quote=${encodedMessage}`;
          break;
        case 'twitter':
          shareUrl = `https://twitter.com/intent/tweet?text=${encodedMessage}`;
          break;
        case 'whatsapp':
          shareUrl = `https://api.whatsapp.com/send?text=${encodedMessage}`;
          break;
        case 'linkedin':
          shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(detailPage)}`;
          break;
        default:
          navigator.clipboard.writeText(message)
            .then(() => alert('✅ Share message copied to clipboard'))
            .catch(() => console.warn('Clipboard unavailable'));
          return;
      }

      window.open(shareUrl, '_blank', 'noopener,noreferrer,width=600,height=500');
      opt.closest('.share-popup')?.classList.add('hidden');
    });
  });
// === News card click to open detail page ===
document.querySelectorAll('.news-card, article[data-title]').forEach(card => {
  card.addEventListener('click', e => {
    if (e.target.closest('.share-btn') || e.target.closest('.share-popup')) return; // Prevent conflict

    const title = card.dataset.title || 'Untitled';
    const date = card.dataset.date || '';
    const image = card.dataset.image || '';
    const description = card.dataset.description || '';

    const content = `
      <p>${description}</p>
      <p class="mt-4">Stay tuned for more in-depth analysis and updates on this topic.</p>
    `;

    localStorage.setItem('selectedNews', JSON.stringify({ title, date, image, description, content }));
    window.location.href = 'blog_detail.html';
  });
});

})();

document.addEventListener("DOMContentLoaded", function () {
  const selectedNews = JSON.parse(localStorage.getItem("selectedNews"));
  if (!selectedNews) return;

  // Title
  const titleEl = document.getElementById("news-title");
  if (titleEl) titleEl.textContent = selectedNews.title;

  // Category
  const categoryEl = document.getElementById("news-category");
  if (categoryEl)
    categoryEl.innerHTML =
      'Category: <span class="font-medium text-blue-600">' +
      (selectedNews.category || "General") +
      "</span>";

  // Date
  const dateEl = document.getElementById("news-date");
  if (dateEl) dateEl.textContent = "Published: " + (selectedNews.date || "");

  // Description (short paragraph)
  const descEl = document.getElementById("news-description");
  if (descEl) descEl.textContent = selectedNews.description || "";

  // Full content (optional if available)
  const contentEl = document.getElementById("news-content");
  if (contentEl) contentEl.innerHTML = selectedNews.content || "";

  // Image
  const imgEl = document.getElementById("news-image");
  if (imgEl) imgEl.src = selectedNews.image || "";
});






document.addEventListener("DOMContentLoaded", function () {
  // Load selected news from localStorage
  const selectedNews = JSON.parse(localStorage.getItem("selectedNews"));
  if (!selectedNews) return;

  // Populate detail page
  document.getElementById("news-title").textContent = selectedNews.title || "Untitled";
  document.getElementById("news-date").textContent = "Published: " + (selectedNews.date || "");
  document.getElementById("news-description").textContent = selectedNews.description || "";
  document.getElementById("news-image").src = selectedNews.image || "./static/images/default-news.jpg";

  // Set category if present
  const cat = document.getElementById("news-category");
  if (cat)
    cat.innerHTML = 'Category: <span class="font-medium text-blue-600">' +
      (selectedNews.category || "General") + "</span>";

  // === SHARE BUTTONS LOGIC ===
  const detailUrl = window.location.href;
  const title = selectedNews.title || "News Update";
  const description = (selectedNews.description || "").slice(0, 120);
  const message = `**${title}**\n\n${description}...\n\nRead more: ${detailUrl}`;
  const encodedMessage = encodeURIComponent(message);

  document.querySelectorAll("button[data-platform]").forEach(btn => {
    btn.addEventListener("click", () => {
      let shareUrl = "";

      switch (btn.dataset.platform) {
        case "facebook":
          shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(detailUrl)}&quote=${encodedMessage}`;
          break;
        case "twitter":
          shareUrl = `https://twitter.com/intent/tweet?text=${encodedMessage}`;
          break;
        case "whatsapp":
          shareUrl = `https://api.whatsapp.com/send?text=${encodedMessage}`;
          break;
        case "linkedin":
          shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(detailUrl)}`;
          break;
      }

      if (shareUrl) {
        window.open(shareUrl, "_blank", "noopener,noreferrer,width=600,height=500");
      }
    });
  });
});





// =============================
// BLOG PAGE INTERACTIONS
// =============================

// --- FILTER BUTTONS ---
const filterButtons = document.querySelectorAll(".filter-btn");
const cards = document.querySelectorAll(".news-card");

filterButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    // Remove active styles from all buttons
    filterButtons.forEach((b) => {
      b.classList.remove("bg-black", "text-white");
      b.classList.add("bg-white", "border");
    });

    // Add active style to clicked button
    btn.classList.remove("bg-white", "border");
    btn.classList.add("bg-black", "text-white");

    // Get selected category
    const selectedCategory = btn.dataset.category;

    // Show/Hide cards with fade transition
    cards.forEach((card) => {
      const cardCategory = card.dataset.category;
      if (selectedCategory === "all" || cardCategory === selectedCategory) {
        card.classList.remove("hidden", "opacity-0", "scale-95");
        card.classList.add("opacity-100", "scale-100");
      } else {
        card.classList.add("opacity-0", "scale-95");
        setTimeout(() => card.classList.add("hidden"), 200);
      }
    });
  });
});

// =============================
// MODAL FUNCTIONALITY
// =============================

// Get modal elements
const readButtons = document.querySelectorAll(".read-btn");
const modal = document.getElementById("newsModal");
const closeModal = document.getElementById("closeModal");
const modalImg = document.getElementById("modalImg");
const modalMeta = document.getElementById("modalMeta");
const modalTitle = document.getElementById("modalTitle");
const modalContent = document.getElementById("modalContent");

// Add click event to all "Read More" buttons
readButtons.forEach(btn => {
  btn.addEventListener("click", (e) => {
    const card = e.target.closest(".news-card");
    if (!card) return;

    // Get data from card
    const img = card.dataset.img || card.querySelector("img")?.src || "";
    const date = card.dataset.date || "";
    const category = card.dataset.categoryName || card.dataset.category || "";
    const title = card.dataset.title || card.querySelector("h2")?.textContent || "";
    const content = (card.dataset.content || "").split("|").filter(Boolean);

    // Set modal data
    if (modalImg) modalImg.src = img;
    if (modalMeta) modalMeta.textContent = `${category} • ${date}`;
    if (modalTitle) modalTitle.textContent = title;
    if (modalContent)
      modalContent.innerHTML =
        content.length > 0
          ? content.map(p => `<p class="mb-3 text-gray-700 leading-relaxed">${p}</p>`).join("")
          : card.querySelector("p.text-gray-600")?.textContent || "";

    // Show modal with fade-in effect
    modal.classList.remove("hidden", "opacity-0");
    setTimeout(() => {
      modal.classList.add("opacity-100");
    }, 10);
  });
});

// --- CLOSE MODAL ---
if (closeModal) {
  closeModal.addEventListener("click", () => {
    modal.classList.remove("opacity-100");
    modal.classList.add("opacity-0");
    setTimeout(() => modal.classList.add("hidden"), 200);
  });
}

// --- CLOSE MODAL ON OUTSIDE CLICK ---
if (modal) {
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("opacity-100");
      modal.classList.add("opacity-0");
      setTimeout(() => modal.classList.add("hidden"), 200);
    }
  });
}
