document.addEventListener("DOMContentLoaded", () => {
	console.log("SIteCoded landing page loaded.");

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

	const pastCarousel = document.getElementById("pastPhotosCarousel");
	if (!pastCarousel) return;

	const photoSources = JSON.parse(pastCarousel.dataset.photos || "[]");

	const prevPhoto = pastCarousel.querySelector(".past-photo-prev");
	const centerPhoto = pastCarousel.querySelector(".past-photo-center");
	const nextPhoto = pastCarousel.querySelector(".past-photo-next");
	if (!prevPhoto || !centerPhoto || !nextPhoto || photoSources.length < 3) return;

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
	};

	const moveNext = () => {
		centerIndex = wrapIndex(centerIndex + 1);
		renderPhotos();
	};

	const movePrev = () => {
		centerIndex = wrapIndex(centerIndex - 1);
		renderPhotos();
	};

	const restartAutoplay = () => {
		if (autoplayTimer) window.clearInterval(autoplayTimer);
		if (pastCarousel.dataset.autoplay === "false") return;
		autoplayTimer = window.setInterval(moveNext, intervalMs);
	};

	renderPhotos();
	restartAutoplay();

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
