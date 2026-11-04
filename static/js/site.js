(() => {
    'use strict';
    const root = document.documentElement;
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
    const themeToggle = document.getElementById('theme-toggle');
    let map;
    let tiles;
    const markers = new Map();
    const updateTheme = () => {
        const dark = root.classList.contains('dark');
        themeToggle.setAttribute('aria-pressed', String(dark));
        themeToggle.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    };
    updateTheme();
    themeToggle.addEventListener('click', () => {
        root.classList.toggle('dark');
        try { localStorage.setItem('theme', root.classList.contains('dark') ? 'dark' : 'light'); } catch (_) { /* Theme works without storage. */ }
        updateTheme();
    });
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        try { if (localStorage.getItem('theme')) return; } catch (_) { /* Follow the system when storage is unavailable. */ }
        root.classList.toggle('dark', event.matches);
        updateTheme();
    });

    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const closeMenu = () => {
        navMenu.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.setAttribute('aria-label', 'Open navigation');
    };
    navToggle.addEventListener('click', () => {
        const open = navMenu.classList.toggle('open');
        navToggle.setAttribute('aria-expanded', String(open));
        navToggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    navMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('click', event => {
        if (!event.target.closest('nav')) closeMenu();
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && navMenu.classList.contains('open')) { closeMenu(); navToggle.focus(); }
    });
    matchMedia('(min-width: 701px)').addEventListener('change', closeMenu);
    const navLinks = [...navMenu.querySelectorAll('a')];
    const sections = [...document.querySelectorAll('main > section[id]')];
    let scrollPending = false;
    function updateActiveSection() {
        const current = sections.filter(section => section.getBoundingClientRect().top <= 160).at(-1);
        navLinks.forEach(link => {
            const active = link.hash === `#${current?.id}`;
            link.classList.toggle('active', active);
            if (active) link.setAttribute('aria-current', 'location');
            else link.removeAttribute('aria-current');
        });
        scrollPending = false;
    }
    addEventListener('scroll', () => {
        if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateActiveSection); }
    }, { passive: true });
    updateActiveSection();
    document.getElementById('current-year').textContent = new Date().getFullYear();

    const copyButton = document.getElementById('copy-email');
    const copyStatus = document.getElementById('copy-status');
    let copyTimeout;
    copyButton.addEventListener('click', async () => {
        clearTimeout(copyTimeout);
        try {
            await navigator.clipboard.writeText('i@yixiao-tao.com');
            copyStatus.textContent = 'Email copied.';
        } catch (_) {
            copyStatus.textContent = 'Select to copy: i@yixiao-tao.com';
        }
        copyTimeout = setTimeout(() => { copyStatus.textContent = ''; }, 5000);
    });

    const dialog = document.getElementById('photo-dialog');
    const dialogImage = document.getElementById('dialog-image');
    const galleryFiles = JSON.parse(document.getElementById('gallery-data').textContent);
    const thumbByFile = new Map(galleryFiles.filter(entry => entry.thumb).map(entry => [entry.file, entry.thumb]));
    const cityImage = path => `/static/images/cities/${path.split('/').map(encodeURIComponent).join('/')}`;
    const photoURL = city => cityImage(city.photo);
    // Cards and popups use the small WebP made by scripts/make_thumbs.py when present.
    const thumbURL = city => cityImage(thumbByFile.get(city.photo) || city.photo);
    const dialogNav = dialog.querySelector('.dialog-nav');
    const dialogPosition = document.getElementById('dialog-position');
    let dialogIndex = -1;
    let galleryPhotos = [];
    function showPhoto(city) {
        dialogIndex = galleryPhotos.findIndex(photo => photo.photo === city.photo);
        dialogNav.hidden = dialogIndex < 0 || galleryPhotos.length < 2;
        if (dialogIndex >= 0) dialogPosition.textContent = `${dialogIndex + 1} / ${galleryPhotos.length}`;
        dialogImage.src = photoURL(city);
        dialogImage.alt = `${city.name} — travel photograph`;
        document.getElementById('photo-title').textContent = city.name;
        document.getElementById('photo-country').textContent = city.country;
        if (!dialog.open) dialog.showModal();
        document.body.style.overflow = 'hidden';
    }
    function stepPhoto(direction) {
        if (dialogIndex < 0 || galleryPhotos.length < 2) return;
        showPhoto(galleryPhotos[(dialogIndex + direction + galleryPhotos.length) % galleryPhotos.length]);
    }
    document.getElementById('dialog-prev').addEventListener('click', () => stepPhoto(-1));
    document.getElementById('dialog-next').addEventListener('click', () => stepPhoto(1));
    dialog.addEventListener('keydown', event => {
        if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
            event.preventDefault();
            stepPhoto(event.key === 'ArrowRight' ? 1 : -1);
        }
    });
    dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { document.body.style.overflow = ''; });
    dialog.addEventListener('click', event => {
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
    const journal = document.getElementById('photo-journal');
    const galleryControls = document.getElementById('gallery-controls');
    const galleryPrevious = document.getElementById('gallery-prev');
    const galleryNext = document.getElementById('gallery-next');
    const galleryPosition = document.getElementById('gallery-position');
    const galleryKey = name => name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/ø/g, 'o').replace(/[^\p{L}\p{N}]/gu, '');
    const photoStem = filename => filename.replace(/\.[^.]+$/, '');
    const cityByPhoto = new Map();
    cities.forEach(city => {
        cityByPhoto.set(galleryKey(city.name), city);
        if (city.photo) cityByPhoto.set(galleryKey(photoStem(city.photo)), city);
    });
    const featuredCities = ['London', 'Tromsø', 'Tokyo'];
    galleryPhotos = galleryFiles.map(({ file: filename }) => {
        const stem = photoStem(filename);
        const city = cityByPhoto.get(galleryKey(stem)) || cityByPhoto.get(galleryKey(stem.replace(/[-_ ]\d+$/, '')));
        return { name: city?.name || stem.replace(/_/g, ' '), country: city?.country || '', photo: filename };
    }).sort((a, b) => {
        const priority = city => featuredCities.includes(city.name) ? featuredCities.indexOf(city.name) : featuredCities.length;
        return priority(a) - priority(b) || a.name.localeCompare(b.name, 'en') || a.photo.localeCompare(b.photo, 'en', { numeric: true });
    });
    galleryPhotos.forEach(city => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'photo-card';
        button.setAttribute('aria-label', `View photograph of ${city.name}`);
        const photo = document.createElement('img');
        photo.src = thumbURL(city);
        photo.alt = [city.name, city.country].filter(Boolean).join(', ');
        photo.loading = 'lazy';
        photo.decoding = 'async';
        photo.draggable = false;
        photo.width = 400;
        photo.height = 260;
        const label = document.createElement('span');
        label.className = 'photo-card-label';
        const title = document.createElement('span');
        title.textContent = city.name;
        if (city.country) {
            const country = document.createElement('small');
            country.textContent = city.country;
            title.append(country);
        }
        label.append(title);
        button.append(photo, label);
        button.addEventListener('click', () => showPhoto(city));
        journal.append(button);
    });
    const photoCards = [...journal.children];
    galleryControls.hidden = photoCards.length === 0;
    journal.hidden = photoCards.length === 0;
    document.getElementById('gallery-empty').hidden = photoCards.length !== 0;
    function updateGallery() {
        const viewport = journal.getBoundingClientRect();
        const visible = photoCards.map((card, index) => ({ index, rect: card.getBoundingClientRect() }))
            .filter(({ rect }) => rect.right > viewport.left + 2 && rect.left < viewport.right - 2);
        const first = (visible[0]?.index ?? 0) + 1;
        const last = (visible.at(-1)?.index ?? 0) + 1;
        galleryPosition.textContent = `${first === last ? first : `${first}–${last}`} / ${photoCards.length}`;
        galleryPrevious.disabled = journal.scrollLeft <= 2;
        galleryNext.disabled = journal.scrollLeft >= journal.scrollWidth - journal.clientWidth - 2;
    }
    function scrollGallery(direction) {
        if (!photoCards.length) return;
        const gap = parseFloat(getComputedStyle(journal).columnGap) || 0;
        const stride = photoCards[0].getBoundingClientRect().width + gap;
        const perPage = Math.max(1, Math.floor((journal.clientWidth + gap + 1) / stride));
        const index = Math.round(journal.scrollLeft / stride) + direction * perPage;
        journal.scrollTo({ left: Math.max(0, index * stride), behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    }
    galleryPrevious.addEventListener('click', () => scrollGallery(-1));
    galleryNext.addEventListener('click', () => scrollGallery(1));
    journal.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !photoCards.length) return;
        event.preventDefault();
        const focused = photoCards.indexOf(document.activeElement);
        const current = focused >= 0 ? focused : Math.round(journal.scrollLeft / (photoCards[0].getBoundingClientRect().width + (parseFloat(getComputedStyle(journal).columnGap) || 0)));
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? photoCards.length - 1 : current + (event.key === 'ArrowRight' ? 1 : -1);
        const card = photoCards[Math.max(0, Math.min(photoCards.length - 1, next))];
        card.focus({ preventScroll: true });
        const left = card.getBoundingClientRect().left - journal.getBoundingClientRect().left + journal.scrollLeft;
        journal.scrollTo({ left, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    });
    let galleryPending = false;
    journal.addEventListener('scroll', () => {
        if (galleryPending) return;
        galleryPending = true;
        requestAnimationFrame(() => { updateGallery(); galleryPending = false; });
    }, { passive: true });
    new ResizeObserver(updateGallery).observe(journal);
    updateGallery();
    const countries = new Set(cities.map(city => city.country));
    document.getElementById('travel-stats').innerHTML = `<strong>${cities.length}</strong> places <span aria-hidden="true"> / </span> <strong>${countries.size}</strong> countries &amp; regions`;
    const list = document.getElementById('city-list');
    const search = document.getElementById('city-search');
    const searchStatus = document.getElementById('search-status');
    const mapElement = document.getElementById('map');
    let mapReady;
    let mapUnavailable = false;
    const openedCountries = new Set();
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ø/g, 'o').toLowerCase();
    function renderCities() {
        const query = normalize(search.value.trim());
        const filtered = cities.filter(city => normalize(`${city.name} ${city.country} ${city.note}`).includes(query));
        const groups = new Map();
        filtered.forEach(city => {
            if (!groups.has(city.country)) groups.set(city.country, []);
            groups.get(city.country).push(city);
        });
        list.replaceChildren();
        groups.forEach((group, country) => {
            const details = document.createElement('details');
            details.className = 'country-group';
            details.open = Boolean(query) || openedCountries.has(country);
            const summary = document.createElement('summary');
            const flag = document.createElement('img');
            flag.className = 'country-flag';
            flag.src = `https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/4x3/${group[0].fi}.svg`;
            flag.alt = '';
            flag.setAttribute('aria-hidden', 'true');
            flag.width = 20;
            flag.height = 15;
            flag.loading = 'lazy';
            const name = document.createElement('span');
            name.textContent = country;
            const count = document.createElement('span');
            count.className = 'country-count';
            count.textContent = group.length;
            count.setAttribute('aria-label', `${group.length} places`);
            summary.append(flag, name, count);
            const buttons = document.createElement('div');
            buttons.className = 'city-buttons';
            group.forEach(city => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'city-button';
                button.textContent = city.name;
                if (city.note) {
                    const note = document.createElement('small');
                    note.textContent = ` · ${city.note}`;
                    button.append(note);
                }
                button.addEventListener('click', () => focusCity(city));
                buttons.append(button);
            });
            details.append(summary, buttons);
            details.addEventListener('toggle', () => {
                if (!query && details.isConnected) {
                    if (details.open) openedCountries.add(country);
                    else openedCountries.delete(country);
                }
            });
            list.append(details);
        });
        searchStatus.textContent = query ? `${filtered.length} ${filtered.length === 1 ? 'place' : 'places'} found` : '';
    }
    renderCities();
    search.addEventListener('input', renderCities);

    function mapFallback() {
        mapUnavailable = true;
        mapElement.replaceChildren();
        const message = document.createElement('p');
        message.className = 'map-status';
        message.textContent = 'The map is unavailable. You can still browse all places below and open the travel photographs above.';
        message.setAttribute('role', 'status');
        mapElement.append(message);
    }
    function loadMap() {
        if (mapReady) return mapReady;
        mapReady = new Promise(resolve => {
            // Leaflet's stylesheet loads with the map instead of blocking first paint.
            const stylesheet = document.createElement('link');
            stylesheet.rel = 'stylesheet';
            stylesheet.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            stylesheet.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
            stylesheet.crossOrigin = '';
            document.head.append(stylesheet);
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
            script.crossOrigin = '';
            let settled = false;
            const timeout = setTimeout(fail, 12000);
            function fail() {
                if (settled) return;
                settled = true;
                clearTimeout(timeout);
                mapFallback();
                resolve(false);
            }
            script.onerror = fail;
            script.onload = () => {
                if (settled) return;
                if (!window.L) { fail(); return; }
                settled = true;
                clearTimeout(timeout);
                mapElement.replaceChildren();
                map = L.map('map', { scrollWheelZoom: false, fadeAnimation: !reducedMotion.matches, zoomAnimation: !reducedMotion.matches }).setView([28, 35], 2);
                tiles = L.tileLayer(mapElement.dataset.tileUrl, {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    maxZoom: 18
                }).addTo(map);
                const notice = document.createElement('p');
                notice.className = 'map-notice';
                notice.setAttribute('role', 'status');
                notice.hidden = true;
                notice.textContent = 'Some map tiles could not load. Place markers still work.';
                mapElement.append(notice);
                tiles.on('tileerror', () => { notice.hidden = false; });
                tiles.on('load', () => {
                    const images = [...mapElement.querySelectorAll('.leaflet-tile')];
                    notice.hidden = images.length > 0 && images.every(image => image.complete && image.naturalWidth > 0);
                });
                const icon = L.divIcon({ className: 'city-marker', iconSize: [10, 10], iconAnchor: [5, 5] });
                cities.forEach(city => {
                    const popup = document.createElement('div');
                    if (city.photo) {
                        const img = document.createElement('img');
                        img.src = thumbURL(city);
                        img.alt = city.name;
                        img.loading = 'lazy';
                        popup.append(img);
                    }
                    const label = document.createElement('div');
                    label.className = 'popup-label';
                    label.textContent = city.name;
                    if (city.note) {
                        const note = document.createElement('span');
                        note.className = 'popup-note';
                        note.textContent = city.note;
                        label.append(note);
                    }
                    popup.append(label);
                    const marker = L.marker([city.lat, city.lng], { icon, title: city.name, alt: city.name }).addTo(map);
                    marker.bindPopup(popup, { className: city.photo ? 'city-photo-popup' : '', maxWidth: 230 });
                    markers.set(city.name, marker);
                });
                document.getElementById('reset-map').hidden = false;
                resolve(true);
            };
            document.head.append(script);
        });
        return mapReady;
    }
    let focusRequest = 0;
    async function focusCity(city) {
        const request = ++focusRequest;
        if (!mapUnavailable) await loadMap();
        if (request !== focusRequest) return;
        if (!map) {
            if (city.photo) showPhoto(city);
            else searchStatus.textContent = `${city.name} · ${city.country}`;
            return;
        }
        map.stop();
        map.closePopup();
        const marker = markers.get(city.name);
        // setView avoids races when users choose several cities in quick succession.
        map.setView([city.lat, city.lng], 10, { animate: false });
        marker.openPopup();
        mapElement.scrollIntoView({ behavior: reducedMotion.matches ? 'instant' : 'smooth', block: 'center' });
    }
    document.getElementById('reset-map').addEventListener('click', () => {
        focusRequest++;
        if (!map) return;
        map.closePopup();
        map.setView([28, 35], 2, { animate: !reducedMotion.matches });
    });
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(entries => {
            if (entries.some(entry => entry.isIntersecting)) { loadMap(); observer.disconnect(); }
        }, { rootMargin: '0px' });
        observer.observe(mapElement);
    } else { loadMap(); }
})();
