/* ═══════════════════════════════════════════════════════════════════════
   CrossFedProto Presentation — JavaScript Controller
   ═══════════════════════════════════════════════════════════════════════ */

const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;
let currentSlide = 0;

// ── Slide Navigation ────────────────────────────────────────────────────

function showSlide(index) {
    if (index < 0 || index >= totalSlides) return;

    slides[currentSlide].classList.remove('active');
    slides[index].classList.add('active');
    currentSlide = index;

    // Update progress bar
    const progress = ((index + 1) / totalSlides) * 100;
    document.getElementById('progressBar').style.width = progress + '%';

    // Update counter
    document.getElementById('slideCounter').textContent = `${index + 1} / ${totalSlides}`;

    // Update nav button states
    document.getElementById('prevBtn').style.opacity = index === 0 ? '0.3' : '1';
    document.getElementById('nextBtn').style.opacity = index === totalSlides - 1 ? '0.3' : '1';
}

function nextSlide() {
    if (currentSlide < totalSlides - 1) {
        showSlide(currentSlide + 1);
    }
}

function prevSlide() {
    if (currentSlide > 0) {
        showSlide(currentSlide - 1);
    }
}

// ── Keyboard Navigation ─────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
        case ' ':
        case 'PageDown':
            e.preventDefault();
            nextSlide();
            break;
        case 'ArrowLeft':
        case 'ArrowUp':
        case 'PageUp':
            e.preventDefault();
            prevSlide();
            break;
        case 'Home':
            e.preventDefault();
            showSlide(0);
            break;
        case 'End':
            e.preventDefault();
            showSlide(totalSlides - 1);
            break;
        case 'f':
        case 'F':
            e.preventDefault();
            toggleFullscreen();
            break;
    }

    // Number keys for quick jump (1-9)
    if (e.key >= '1' && e.key <= '9') {
        const target = parseInt(e.key) - 1;
        if (target < totalSlides) {
            showSlide(target);
        }
    }
});

// ── Touch / Swipe Support ──────────────────────────────────────────────

let touchStartX = 0;
let touchStartY = 0;

document.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
});

document.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].screenX - touchStartX;
    const dy = e.changedTouches[0].screenY - touchStartY;

    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
        if (dx < 0) nextSlide();
        else prevSlide();
    }
});

// ── Mouse Wheel ─────────────────────────────────────────────────────────

let wheelTimeout;
document.addEventListener('wheel', (e) => {
    e.preventDefault();
    if (wheelTimeout) return;

    wheelTimeout = setTimeout(() => {
        wheelTimeout = null;
    }, 500);

    if (e.deltaY > 0) nextSlide();
    else prevSlide();
}, { passive: false });

// ── Fullscreen ──────────────────────────────────────────────────────────

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
    } else {
        document.exitFullscreen().catch(() => {});
    }
}

// ── Initialize ──────────────────────────────────────────────────────────

showSlide(0);

// ── Add slide overview overlay (press 'o') ──────────────────────────────

let overviewActive = false;

document.addEventListener('keydown', (e) => {
    if (e.key === 'o' || e.key === 'O') {
        toggleOverview();
    }
    if (e.key === 'Escape' && overviewActive) {
        toggleOverview();
    }
});

function toggleOverview() {
    overviewActive = !overviewActive;

    let overlay = document.getElementById('slide-overview');
    if (overviewActive) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'slide-overview';
            overlay.style.cssText = `
                position: fixed; inset: 0; z-index: 200;
                background: rgba(3, 7, 18, 0.95);
                backdrop-filter: blur(12px);
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                padding: 40px;
                overflow-y: auto;
            `;

            for (let i = 0; i < totalSlides; i++) {
                const thumb = document.createElement('div');
                const title = slides[i].querySelector('h1, h2');
                thumb.style.cssText = `
                    background: #111827;
                    border: 2px solid ${i === currentSlide ? '#06b6d4' : '#1e293b'};
                    border-radius: 12px;
                    padding: 16px;
                    cursor: pointer;
                    transition: all 0.2s;
                    aspect-ratio: 16/10;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                `;
                thumb.innerHTML = `
                    <div style="font-size: 24px; font-weight: 900; color: #06b6d4; margin-bottom: 8px;">${i + 1}</div>
                    <div style="font-size: 12px; color: #94a3b8;">${title ? title.textContent.substring(0, 50) : 'Slide ' + (i + 1)}</div>
                `;
                thumb.addEventListener('click', () => {
                    showSlide(i);
                    toggleOverview();
                });
                thumb.addEventListener('mouseenter', () => {
                    thumb.style.borderColor = '#06b6d4';
                    thumb.style.transform = 'scale(1.03)';
                });
                thumb.addEventListener('mouseleave', () => {
                    thumb.style.borderColor = i === currentSlide ? '#06b6d4' : '#1e293b';
                    thumb.style.transform = 'scale(1)';
                });
                overlay.appendChild(thumb);
            }

            document.body.appendChild(overlay);
        } else {
            overlay.style.display = 'grid';
        }
    } else {
        if (overlay) overlay.style.display = 'none';
    }
}

// ── Print/Export helper ─────────────────────────────────────────────────

console.log('%c🎨 CrossFedProto Presentation', 'font-size: 20px; font-weight: 900; color: #06b6d4;');
console.log('%cNavigation: ←/→ arrows, Space, Mouse wheel, Touch swipe', 'color: #94a3b8;');
console.log('%cF = Fullscreen | O = Overview | 1-9 = Jump to slide', 'color: #94a3b8;');
