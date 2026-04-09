document.addEventListener("DOMContentLoaded", () => {
	console.log("SIteCoded landing page loaded.");

	const landing12Nav = document.querySelector(".landing12-nav");
	if (landing12Nav) {
		const toggle = landing12Nav.querySelector(".landing12-menu-toggle");
		const menu = landing12Nav.querySelector(".landing12-links");
		const backdrop = landing12Nav.querySelector(".landing12-menu-backdrop");

		if (toggle && menu && backdrop) {
			const closeMenu = () => {
				menu.classList.remove("is-open");
				backdrop.classList.remove("is-open");
				toggle.setAttribute("aria-expanded", "false");
				document.body.classList.remove("landing12-no-scroll");
			};

			const openMenu = () => {
				menu.classList.add("is-open");
				backdrop.classList.add("is-open");
				toggle.setAttribute("aria-expanded", "true");
				document.body.classList.add("landing12-no-scroll");
			};

			toggle.addEventListener("click", () => {
				const isOpen = menu.classList.contains("is-open");
				if (isOpen) {
					closeMenu();
				} else {
					openMenu();
				}
			});

			backdrop.addEventListener("click", closeMenu);

			window.addEventListener("keydown", (event) => {
				if (event.key === "Escape") {
					closeMenu();
				}
			});

			menu.querySelectorAll("a").forEach((link) => {
				link.addEventListener("click", closeMenu);
			});

			window.addEventListener("resize", () => {
				if (window.innerWidth > 760) {
					closeMenu();
				}
			});
		}
	}

	const countdowns = document.querySelectorAll("[data-countdown]");
	if (countdowns.length) {
		const updateCountdowns = () => {
			countdowns.forEach((element) => {
				const targetRaw = element.getAttribute("data-countdown-target");
				const targetDate = targetRaw ? new Date(targetRaw) : null;

				if (!targetDate || Number.isNaN(targetDate.getTime())) return;

				const now = new Date();
				const deltaMs = Math.max(0, targetDate.getTime() - now.getTime());

				const totalSeconds = Math.floor(deltaMs / 1000);
				const days = Math.floor(totalSeconds / 86400);
				const hours = Math.floor((totalSeconds % 86400) / 3600);
				const minutes = Math.floor((totalSeconds % 3600) / 60);
				const seconds = totalSeconds % 60;

				const values = {
					days: String(days).padStart(2, "0"),
					hours: String(hours).padStart(2, "0"),
					minutes: String(minutes).padStart(2, "0"),
					seconds: String(seconds).padStart(2, "0"),
				};

				element.classList.toggle("is-live", deltaMs === 0);

				Object.entries(values).forEach(([unit, value]) => {
					const node = element.querySelector(`[data-unit="${unit}"]`);
					if (node) node.textContent = value;
				});
			});
		};

		updateCountdowns();
		window.setInterval(updateCountdowns, 1000);
	}

	const landingPage = document.querySelector(".landing-page");
	if (landingPage && "IntersectionObserver" in window) {
		const sections = landingPage.querySelectorAll("section");
		const observer = new IntersectionObserver((entries) => {
			entries.forEach((entry) => {
				entry.target.classList.toggle("is-inview", entry.isIntersecting);
			});
		}, {
			root: null,
			rootMargin: "-8% 0px -12% 0px",
			threshold: 0.18,
		});

		sections.forEach((section) => observer.observe(section));
	}

	const initGlobalRevealAnimations = () => {
		const main = document.querySelector("main");
		if (!main) return;

		const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		const autoRevealSelector = [
			"main > section",
			"main .speakers-section__grid > *",
			"main .tickets-grid > *",
			"main .accommodations-list > *",
			"main .accommodations-panel__grid > *",
			"main .artist-card",
			"main .faq-item",
			"main .venue-map-poi-list",
			"main .vm-panel",
		].join(", ");

		const blockedAncestorSelector = [
			".landing12-header",
			".landing12-nav",
			".landing12-links",
			".landing12-menu-backdrop",
			"#pastPhotosCarousel",
			".past-carousel-section",
			".social-proof-section",
			".social-proof-row__track",
			".landing12-strip",
			".vm-canvas-wrap",
			"#venue-map",
			"#venue-svg-map",
			".leaflet-container",
			"[data-reveal-ignore]",
		].join(", ");

		const candidates = [
			...document.querySelectorAll("[data-reveal]"),
			...document.querySelectorAll(autoRevealSelector),
		];

		const seen = new Set();
		const revealTargets = candidates.filter((element) => {
			if (!(element instanceof HTMLElement)) return false;
			if (seen.has(element)) return false;
			seen.add(element);

			if (element.closest(blockedAncestorSelector)) return false;
			if (element.hasAttribute("data-reveal-ignore")) return false;

			const parent = element.parentElement;
			if (parent && parent.matches("[data-reveal-group], .speakers-section__grid, .tickets-grid, .accommodations-list, .accommodations-panel__grid")) {
				const siblings = Array.from(parent.children).filter((node) => node instanceof HTMLElement);
				const index = siblings.indexOf(element);
				const clampedIndex = Math.max(0, Math.min(index, 6));
				element.style.setProperty("--reveal-delay", `${clampedIndex * 65}ms`);
			}

			element.classList.add(element.dataset.reveal === "fade" ? "reveal-fade" : "reveal-up");
			return true;
		});

		if (!revealTargets.length) return;

		if (prefersReducedMotion || !("IntersectionObserver" in window)) {
			revealTargets.forEach((element) => element.classList.add("is-revealed"));
			return;
		}

		const observer = new IntersectionObserver((entries, instance) => {
			entries.forEach((entry) => {
				if (!entry.isIntersecting) return;
				entry.target.classList.add("is-revealed");
				instance.unobserve(entry.target);
			});
		}, {
			root: null,
			rootMargin: "0px 0px -10% 0px",
			threshold: 0.16,
		});

		revealTargets.forEach((element) => observer.observe(element));
	};

	initGlobalRevealAnimations();

	const whatImageFrames = document.querySelectorAll(".what-section__media-inner");
	whatImageFrames.forEach((frame) => {
		const imageX = frame.dataset.imageX;
		const imageY = frame.dataset.imageY;
		const imageZoom = frame.dataset.imageZoom;

		if (imageX) {
			frame.style.setProperty("--what-image-x", imageX);
		}

		if (imageY) {
			frame.style.setProperty("--what-image-y", imageY);
		}

		if (imageZoom) {
			frame.style.setProperty("--what-image-zoom", imageZoom);
		}
	});

	const speakerCards = document.querySelectorAll("[data-speaker-card]");
	const normalizeCssLength = (value) => {
		if (value == null) return null;
		const trimmedValue = String(value).trim();
		if (!trimmedValue) return null;

		const hasUnit = /[a-z%]/i.test(trimmedValue);
		if (hasUnit) return trimmedValue;

		return `${trimmedValue}px`;
	};

	speakerCards.forEach((card) => {
		const imageX = normalizeCssLength(card.dataset.imageX);
		const imageY = normalizeCssLength(card.dataset.imageY);

		if (imageX) {
			card.style.setProperty("--speaker-person-offset-x", imageX);
		}

		if (imageY) {
			card.style.setProperty("--speaker-person-offset-y", imageY);
		}
	});

	const pastCarousel = document.getElementById("pastPhotosCarousel");
	if (pastCarousel) {
		const photoSources = JSON.parse(pastCarousel.dataset.photos || "[]");

		const prevPhoto = pastCarousel.querySelector(".past-photo-prev");
		const centerPhoto = pastCarousel.querySelector(".past-photo-center");
		const nextPhoto = pastCarousel.querySelector(".past-photo-next");

		if (prevPhoto && centerPhoto && nextPhoto && photoSources.length >= 3) {
			const prevButton = pastCarousel.querySelector("[data-carousel-prev]");
			const nextButton = pastCarousel.querySelector("[data-carousel-next]");
			const dotsContainer = pastCarousel.querySelector("[data-carousel-dots]");

			let centerIndex = 1;
			let autoplayTimer;
			const intervalMs = Number(pastCarousel.dataset.interval || 3500);
			let touchStartX = 0;
			let touchStartY = 0;

			const wrapIndex = (index) => (index + photoSources.length) % photoSources.length;

			const renderPhotos = () => {
				const prevIndex = wrapIndex(centerIndex - 1);
				const nextIndex = wrapIndex(centerIndex + 1);

				prevPhoto.src = photoSources[prevIndex].src;
				prevPhoto.alt = photoSources[prevIndex].alt;
				centerPhoto.src = photoSources[centerIndex].src;
				centerPhoto.alt = photoSources[centerIndex].alt;
				nextPhoto.src = photoSources[nextIndex].src;
				nextPhoto.alt = photoSources[nextIndex].alt;

				if (dotsContainer) {
					const dots = dotsContainer.querySelectorAll(".past-carousel-dot");
					dots.forEach((dot, dotIndex) => {
						dot.classList.toggle("is-active", dotIndex === centerIndex);
						dot.setAttribute("aria-current", dotIndex === centerIndex ? "true" : "false");
					});
				}
			};

			const goToIndex = (targetIndex) => {
				centerIndex = wrapIndex(targetIndex);
				renderPhotos();
			};

			const moveNext = () => {
				goToIndex(centerIndex + 1);
			};

			const movePrev = () => {
				goToIndex(centerIndex - 1);
			};

			const restartAutoplay = () => {
				if (autoplayTimer) window.clearInterval(autoplayTimer);
				if (pastCarousel.dataset.autoplay === "false") return;
				autoplayTimer = window.setInterval(moveNext, intervalMs);
			};

			renderPhotos();
			restartAutoplay();

			if (dotsContainer) {
				dotsContainer.innerHTML = "";
				photoSources.forEach((photo, index) => {
					const dot = document.createElement("button");
					dot.type = "button";
					dot.className = "past-carousel-dot";
					dot.setAttribute("aria-label", `Show image ${index + 1}`);
					dot.setAttribute("title", photo.alt || `Image ${index + 1}`);
					dot.addEventListener("click", () => {
						goToIndex(index);
						restartAutoplay();
					});
					dotsContainer.appendChild(dot);
				});
				renderPhotos();
			}

			if (prevButton) {
				prevButton.addEventListener("click", () => {
					movePrev();
					restartAutoplay();
				});
			}

			if (nextButton) {
				nextButton.addEventListener("click", () => {
					moveNext();
					restartAutoplay();
				});
			}

			pastCarousel.addEventListener("touchstart", (event) => {
				if (!event.changedTouches.length) return;
				touchStartX = event.changedTouches[0].clientX;
				touchStartY = event.changedTouches[0].clientY;
			}, { passive: true });

			pastCarousel.addEventListener("touchend", (event) => {
				if (!event.changedTouches.length) return;

				const touchEndX = event.changedTouches[0].clientX;
				const touchEndY = event.changedTouches[0].clientY;
				const deltaX = touchEndX - touchStartX;
				const deltaY = touchEndY - touchStartY;

				if (Math.abs(deltaX) < 40 || Math.abs(deltaX) <= Math.abs(deltaY)) return;

				if (deltaX < 0) {
					moveNext();
				} else {
					movePrev();
				}

				restartAutoplay();
			}, { passive: true });

			pastCarousel.addEventListener("mouseenter", () => {
				if (autoplayTimer) window.clearInterval(autoplayTimer);
			});

			pastCarousel.addEventListener("mouseleave", restartAutoplay);
		}
	}
});
