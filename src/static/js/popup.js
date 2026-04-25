/* =========================================================
   Promo Modal — popup.js
   Triggers:
     - Landing page: 50% scroll depth (fires once per visit)
     - Tickets page:  1s delay on page load
   Suppression: localStorage key "promoSuppressed"
   ========================================================= */

(function () {
    'use strict';

    var STORAGE_KEY = 'promoSuppressed';
    var SCROLL_THRESHOLD = 0.5; // 50%

    document.addEventListener('DOMContentLoaded', function () {

        // Don't show if user opted out
        if (localStorage.getItem(STORAGE_KEY) === 'true') return;

        var modal = document.querySelector('[data-promo-modal]');
        if (!modal) return;

        var suppressCheck = document.getElementById('promo-suppress');
        var hasTriggered = false;

        // ---- Open / Close ----

        function openModal() {
            if (hasTriggered) return;
            hasTriggered = true;

            modal.removeAttribute('hidden');
            modal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('landing12-no-scroll');
        }

        function closeModal() {
            if (suppressCheck && suppressCheck.checked) {
                localStorage.setItem(STORAGE_KEY, 'true');
            }
            modal.setAttribute('hidden', '');
            modal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('landing12-no-scroll');
        }

        // ---- Close triggers ----

        // Backdrop + close button(s) via data attribute
        modal.addEventListener('click', function (e) {
            if (e.target.closest('[data-promo-close]')) {
                closeModal();
            }
        });

        // Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !modal.hasAttribute('hidden')) {
                closeModal();
            }
        });

        // ---- Page detection ----

        var isLanding = !!document.querySelector('.landing12') || !!document.querySelector('[data-landing12]');
        var isTickets = !!document.querySelector('.tickets-page');

        if (isLanding) {
            // Trigger at 50% scroll depth — one-shot listener
            function onScroll() {
                var scrolled = window.scrollY;
                var docHeight = document.documentElement.scrollHeight - window.innerHeight;
                if (docHeight <= 0) return;

                if (scrolled / docHeight >= SCROLL_THRESHOLD) {
                    window.removeEventListener('scroll', onScroll, { passive: true });
                    openModal();
                }
            }
            window.addEventListener('scroll', onScroll, { passive: true });
        }
    });

}());
