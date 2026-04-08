document.addEventListener("DOMContentLoaded", () => {
	console.log("SIteCoded landing page loaded.");

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
	if (!pastCarousel) return;

	const photoSources = JSON.parse(pastCarousel.dataset.photos || "[]");

	const prevPhoto = pastCarousel.querySelector(".past-photo-prev");
	const centerPhoto = pastCarousel.querySelector(".past-photo-center");
	const nextPhoto = pastCarousel.querySelector(".past-photo-next");
	if (!prevPhoto || !centerPhoto || !nextPhoto || photoSources.length < 3) return;

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
});
