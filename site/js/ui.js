/* OpenShelter UI chrome, theme toggle, scroll reveal, back-to-top. No dependencies. */
(function () {
 const root = document.documentElement;
 root.classList.add('js-ready');
 // Theme: stored choice > OS preference, applied ASAP to avoid flash-of-wrong-theme
 try {
 const saved = localStorage.getItem('os-theme');
 if (saved === 'dark' || saved === 'light') root.setAttribute('data-theme', saved);
 } catch (_) {}
 const mq = window.matchMedia('(prefers-color-scheme: dark)');
 function isDark() { return (root.getAttribute('data-theme') || (mq.matches ? 'dark' : 'light')) === 'dark'; }
 function syncMeta() {
 const m = document.querySelector('meta[name="theme-color"]');
 if (m) m.setAttribute('content', isDark() ? '#0b1a22' : '#0b6e66');
 }
 function syncIcon() {
 document.querySelectorAll('.theme-toggle').forEach(b => {
 b.setAttribute('aria-label', isDark() ? 'Switch to light mode' : 'Switch to dark mode');
 });
 syncMeta();
 }
 document.addEventListener('click', e => {
 if (!e.target.closest('.theme-toggle')) return;
 root.setAttribute('data-theme', isDark() ? 'light' : 'dark');
 try { localStorage.setItem('os-theme', root.getAttribute('data-theme')); } catch (_) {}
 syncIcon();
 });
 mq.addEventListener && mq.addEventListener('change', syncIcon);
 addEventListener('DOMContentLoaded', syncIcon);
 // Scroll reveal
 if ('IntersectionObserver' in window) {
 const io = new IntersectionObserver(es => es.forEach(en => {
 if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
 }), { threshold: 0.12 });
 document.querySelectorAll('.reveal').forEach(el => io.observe(el));
 } else document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
 // Back to top
 const tt = document.querySelector('.totop');
 if (tt) {
 addEventListener('scroll', () => tt.classList.toggle('show', scrollY > 700), { passive: true });
 tt.addEventListener('click', () => scrollTo({ top: 0, behavior: 'smooth' }));
 }
})();

/* v3: mobile nav toggle */
(function(){
 const t = document.querySelector('.nav-toggle'), n = document.querySelector('.nav');
 if (t && n) t.addEventListener('click', () => {
 const open = n.classList.toggle('open');
 t.setAttribute('aria-expanded', open ? 'true' : 'false');
 });
})();
