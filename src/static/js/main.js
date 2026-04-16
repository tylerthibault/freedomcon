document.addEventListener("DOMContentLoaded", () => {
	console.log("SIteCoded landing page loaded.");

	const landing12Nav = document.querySelector(".landing12-nav");
	if (landing12Nav) {
		const mobileNavQuery = window.matchMedia("(max-width: 760px)");
		let landing12LastScrollY = window.scrollY;
		let landing12ScrollTicking = false;

		const syncLanding12MobileNavState = () => {
			landing12ScrollTicking = false;

			if (!mobileNavQuery.matches) {
				landing12Nav.classList.remove("is-condensed");
				landing12Nav.classList.remove("is-at-top");
				landing12LastScrollY = window.scrollY;
				return;
			}

			const currentScrollY = Math.max(window.scrollY, 0);
			const isAtTop = currentScrollY <= 24;
			landing12Nav.classList.toggle("is-at-top", isAtTop);

			if (isAtTop) {
				landing12Nav.classList.add("is-condensed");
				landing12LastScrollY = currentScrollY;
				return;
			}

			const scrollDelta = currentScrollY - landing12LastScrollY;

			if (Math.abs(scrollDelta) < 4) {
				return;
			}

			if (scrollDelta > 0 && currentScrollY > 24) {
				landing12Nav.classList.add("is-condensed");
			} else if (scrollDelta < 0 || currentScrollY <= 24) {
				landing12Nav.classList.remove("is-condensed");
			}

			landing12LastScrollY = currentScrollY;
		};

		const requestLanding12MobileNavStateSync = () => {
			if (landing12ScrollTicking) {
				return;
			}

			landing12ScrollTicking = true;
			window.requestAnimationFrame(syncLanding12MobileNavState);
		};

		window.addEventListener("scroll", requestLanding12MobileNavStateSync, { passive: true });
		window.addEventListener("resize", syncLanding12MobileNavState);
		if (typeof mobileNavQuery.addEventListener === "function") {
			mobileNavQuery.addEventListener("change", syncLanding12MobileNavState);
		}
		syncLanding12MobileNavState();

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

	const initDeclarationWordHover = () => {
		const supportsFinePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
		if (!supportsFinePointer) return;

		const container = document.querySelector("[data-declaration-bg]");
		if (!(container instanceof HTMLElement)) return;

		const words = Array.from(container.querySelectorAll(".landing12-declaration-bg__word"));
		if (!words.length) return;

		let activeWord = null;
		let wordRects = [];
		let frameId = 0;
		let pointerX = 0;
		let pointerY = 0;
		let measureFrameId = 0;

		const measureWordRects = () => {
			measureFrameId = 0;
			wordRects = words
				.map((word) => ({ word, rect: word.getBoundingClientRect() }))
				.filter(({ rect }) => rect.width > 0 && rect.height > 0);
		};

		const requestMeasure = () => {
			if (measureFrameId) return;
			measureFrameId = window.requestAnimationFrame(measureWordRects);
		};

		const setActiveWord = (word) => {
			if (activeWord === word) return;
			if (activeWord) activeWord.classList.remove("is-active");
			activeWord = word;
			if (activeWord) activeWord.classList.add("is-active");
		};

		const updateFromPointer = () => {
			frameId = 0;

			let hoveredWord = null;
			for (let index = 0; index < wordRects.length; index += 1) {
				const entry = wordRects[index];
				const rect = entry.rect;
				if (
					pointerX >= rect.left &&
					pointerX <= rect.right &&
					pointerY >= rect.top &&
					pointerY <= rect.bottom
				) {
					hoveredWord = entry.word;
					break;
				}
			}

			setActiveWord(hoveredWord);
		};

		const queueUpdate = (event) => {
			pointerX = event.clientX;
			pointerY = event.clientY;
			if (frameId) return;
			frameId = window.requestAnimationFrame(updateFromPointer);
		};

		measureWordRects();
		window.addEventListener("pointermove", queueUpdate, { passive: true });
		window.addEventListener("scroll", requestMeasure, { passive: true });
		window.addEventListener("resize", requestMeasure);
		window.addEventListener("blur", () => setActiveWord(null));
	};

	initDeclarationWordHover();

	const initCrowderParallax = () => {
		const section = document.querySelector("[data-crowder-parallax]");
		if (!(section instanceof HTMLElement)) return;

		const backgroundLayer = section.querySelector("[data-crowder-parallax-bg]");
		if (!(backgroundLayer instanceof HTMLElement)) return;

		let frameId = 0;

		const getMaxOffset = () => {
			const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
			if (viewportWidth <= 760) return 150;
			if (viewportWidth <= 1100) return 200;
			return 260;
		};

		const update = () => {
			frameId = 0;
			const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
			const rect = section.getBoundingClientRect();
			const maxOffset = getMaxOffset();
			const progress = (viewportHeight - rect.top) / (viewportHeight + rect.height);
			const clampedProgress = Math.min(1, Math.max(0, progress));
			const offset = clampedProgress * maxOffset;

			backgroundLayer.style.transform = `translate3d(0, ${offset.toFixed(2)}px, 0) scale(1.18)`;
		};

		const requestUpdate = () => {
			if (frameId) return;
			frameId = window.requestAnimationFrame(update);
		};

		update();
		window.addEventListener("scroll", requestUpdate, { passive: true });
		window.addEventListener("resize", requestUpdate);
	};

	initCrowderParallax();

	const initCrowderAudioPlayer = () => {
		const wrapper = document.querySelector("[data-crowder-audio]");
		if (!(wrapper instanceof HTMLElement)) return;

		const toggleButton = wrapper.querySelector("[data-crowder-audio-toggle]");
		const panel = wrapper.querySelector("[data-crowder-audio-panel]");
		const closeButton = wrapper.querySelector("[data-crowder-audio-close]");
		const player = wrapper.querySelector("[data-crowder-audio-player]");

		if (!(toggleButton instanceof HTMLButtonElement) || !(panel instanceof HTMLElement)) return;

		const openPanel = () => {
			panel.removeAttribute("hidden");
			toggleButton.setAttribute("aria-expanded", "true");

			if (player instanceof HTMLAudioElement) {
				const playPromise = player.play();
				if (playPromise && typeof playPromise.catch === "function") {
					playPromise.catch(() => undefined);
				}
			}
		};

		const closePanel = () => {
			panel.setAttribute("hidden", "");
			toggleButton.setAttribute("aria-expanded", "false");

			if (player instanceof HTMLAudioElement) {
				player.pause();
			}
		};

		toggleButton.addEventListener("click", () => {
			const isOpen = !panel.hasAttribute("hidden");
			if (isOpen) {
				closePanel();
				return;
			}

			openPanel();
		});

		if (closeButton instanceof HTMLButtonElement) {
			closeButton.addEventListener("click", closePanel);
		}
	};

	initCrowderAudioPlayer();

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

	const normalizeScale = (value) => {
		if (value == null) return null;
		const trimmedValue = String(value).trim();
		if (!trimmedValue) return null;

		const numericValue = Number(trimmedValue);
		if (Number.isNaN(numericValue) || numericValue <= 0) return null;

		return String(numericValue);
	};

	const applyClipPathToCard = (card) => {
		const personShell = card.querySelector(".speaker-card__person-shell");
		const imageShell = card.querySelector(".speaker-card__image-shell");
		if (!personShell || !imageShell) return;

		const W = imageShell.offsetWidth;
		const H = imageShell.offsetHeight;
		if (!W || !H) return; // card is hidden, skip

		const big = 9999;
		const L = 0.03 * W;
		const R = 0.97 * W;
		const B = H;
		const r = 0.14 * 0.94 * W;

		const d = [
			`M -${big},-${big}`,
			`L ${W + big},-${big}`,
			`L ${W + big},${B - r}`,
			`L ${R},${B - r}`,
			`A ${r},${r},0,0,1,${R - r},${B}`,
			`L ${L + r},${B}`,
			`A ${r},${r},0,0,1,${L},${B - r}`,
			`L -${big},${B - r}`,
			`Z`,
		].join(" ");

		personShell.style.clipPath = `path('${d}')`;
	};

	speakerCards.forEach((card) => {
		const imageX = normalizeCssLength(card.dataset.imageX);
		const imageY = normalizeCssLength(card.dataset.imageY);
		const shrink = normalizeScale(card.dataset.shrink);

		if (imageX) {
			card.style.setProperty("--speaker-person-offset-x", imageX);
		}

		if (imageY) {
			card.style.setProperty("--speaker-person-offset-y", imageY);
		}

		if (shrink) {
			card.style.setProperty("--speaker-person-scale", shrink);
		}

		applyClipPathToCard(card);
	});

	const speakersToggle = document.querySelector("[data-speakers-toggle]");
	const extraSpeakersGrid = document.querySelector("[data-speakers-extra]");
	if (speakersToggle && extraSpeakersGrid) {
		speakersToggle.addEventListener("click", () => {
			const isHidden = extraSpeakersGrid.hasAttribute("hidden");
			if (isHidden) {
				extraSpeakersGrid.removeAttribute("hidden");
				speakersToggle.setAttribute("aria-expanded", "true");
				speakersToggle.textContent = "Show Less";
				// Re-apply clip paths now that cards have real dimensions
				extraSpeakersGrid.querySelectorAll("[data-speaker-card]").forEach(applyClipPathToCard);
				return;
			}

			extraSpeakersGrid.setAttribute("hidden", "");
			speakersToggle.setAttribute("aria-expanded", "false");
			speakersToggle.textContent = "See More";
		});
	}

	const initInteractiveSocialProofMarquee = () => {
		if (window.matchMedia("(max-width: 768px)").matches) {
			return;
		}

		const marqueeContainers = document.querySelectorAll(".social-proof-marquee");
		if (!marqueeContainers.length) return;

		const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

		marqueeContainers.forEach((container) => {
			const configuredSpeed = Number(container.dataset.marqueeSpeed || 78);
			const baseSpeed = Number.isFinite(configuredSpeed) ? Math.max(20, configuredSpeed) : 78;

			container.querySelectorAll(".social-proof-row").forEach((row) => {
				const track = row.querySelector(".social-proof-row__track");
				const group = track ? track.querySelector(".social-proof-row__group") : null;

				if (!(track instanceof HTMLElement) || !(group instanceof HTMLElement)) return;

				row.classList.add("is-interactive");
				track.style.animation = "none";

				const direction = row.classList.contains("social-proof-row--right") ? 1 : -1;
				let groupWidth = Math.max(1, group.getBoundingClientRect().width);
				let position = direction === 1 ? -groupWidth : 0;
				let pointerId = null;
				let dragStartX = 0;
				let dragStartPosition = position;
				let isDragging = false;
				let animationFrameId = 0;
				let lastFrameTime = 0;

				const normalizePosition = (value) => {
					let normalized = value;
					while (normalized <= -groupWidth) normalized += groupWidth;
					while (normalized > 0) normalized -= groupWidth;
					return normalized;
				};

				const applyPosition = () => {
					track.style.transform = `translate3d(${position}px, 0, 0)`;
				};

				const refreshDimensions = () => {
					groupWidth = Math.max(1, group.getBoundingClientRect().width);
					position = normalizePosition(position);
					applyPosition();
				};

				const onFrame = (time) => {
					if (!lastFrameTime) {
						lastFrameTime = time;
					}

					const deltaSeconds = (time - lastFrameTime) / 1000;
					lastFrameTime = time;

					if (!isDragging) {
						position = normalizePosition(position + (direction * baseSpeed * deltaSeconds));
						applyPosition();
					}

					animationFrameId = window.requestAnimationFrame(onFrame);
				};

				const endDrag = () => {
					if (!isDragging) return;
					isDragging = false;
					pointerId = null;
					row.classList.remove("is-dragging");
					lastFrameTime = 0;
				};

				row.addEventListener("pointerdown", (event) => {
					if (event.pointerType === "mouse" && event.button !== 0) return;

					isDragging = true;
					pointerId = event.pointerId;
					dragStartX = event.clientX;
					dragStartPosition = position;
					row.classList.add("is-dragging");
					row.setPointerCapture(event.pointerId);
					event.preventDefault();
				});

				row.addEventListener("pointermove", (event) => {
					if (!isDragging || event.pointerId !== pointerId) return;

					const deltaX = event.clientX - dragStartX;
					position = normalizePosition(dragStartPosition + deltaX);
					applyPosition();
				});

				row.addEventListener("pointerup", (event) => {
					if (event.pointerId !== pointerId) return;
					endDrag();
				});

				row.addEventListener("pointercancel", (event) => {
					if (event.pointerId !== pointerId) return;
					endDrag();
				});

				row.addEventListener("lostpointercapture", endDrag);
				window.addEventListener("resize", refreshDimensions);

				applyPosition();

				if (!prefersReducedMotion) {
					animationFrameId = window.requestAnimationFrame(onFrame);
				}

				row.addEventListener("remove", () => {
					if (animationFrameId) {
						window.cancelAnimationFrame(animationFrameId);
					}
				});
			});
		});
	};

	initInteractiveSocialProofMarquee();

	const socialProofSection = document.querySelector(".social-proof-section");
	const socialProofSeeMoreButton = socialProofSection ? socialProofSection.querySelector("[data-social-proof-see-more]") : null;
	if (socialProofSection && socialProofSeeMoreButton instanceof HTMLButtonElement) {
		const mobileBreakpoint = window.matchMedia("(max-width: 768px)");
		const hasExtraMobileCards = socialProofSection.querySelector(".social-proof-mobile-card--extra") !== null;
		let isMobileExpanded = false;
		let wasMobile = mobileBreakpoint.matches;

		const syncMobileSocialProofState = () => {
			const isMobile = mobileBreakpoint.matches;

			if (isMobile && !wasMobile) {
				isMobileExpanded = false;
			}
			wasMobile = isMobile;

			if (!isMobile || !hasExtraMobileCards) {
				socialProofSection.classList.add("is-mobile-expanded");
				socialProofSeeMoreButton.hidden = true;
				socialProofSeeMoreButton.setAttribute("aria-expanded", "true");
				return;
			}

			socialProofSection.classList.toggle("is-mobile-expanded", isMobileExpanded);
			socialProofSeeMoreButton.hidden = isMobileExpanded;
			socialProofSeeMoreButton.setAttribute("aria-expanded", isMobileExpanded ? "true" : "false");
		};

		socialProofSection.classList.remove("is-mobile-expanded");
		socialProofSeeMoreButton.addEventListener("click", () => {
			isMobileExpanded = true;
			syncMobileSocialProofState();
		});

		syncMobileSocialProofState();
		if (typeof mobileBreakpoint.addEventListener === "function") {
			mobileBreakpoint.addEventListener("change", syncMobileSocialProofState);
		} else {
			mobileBreakpoint.addListener(syncMobileSocialProofState);
		}
	}

	const socialProofModal = document.querySelector("[data-social-proof-modal]");
	if (socialProofModal) {
		document.body.appendChild(socialProofModal);

		const modalName = socialProofModal.querySelector("[data-social-proof-modal-name]");
		const modalTitle = socialProofModal.querySelector("[data-social-proof-modal-title]");
		const modalQuote = socialProofModal.querySelector("[data-social-proof-modal-quote]");
		const modalCloseControls = socialProofModal.querySelectorAll("[data-social-proof-close]");
		const closeButton = socialProofModal.querySelector(".social-proof-modal__close");
		let activeTrigger = null;

		const closeSocialProofModal = () => {
			socialProofModal.setAttribute("hidden", "");
			socialProofModal.setAttribute("aria-hidden", "true");
			document.body.classList.remove("landing12-no-scroll");
			if (activeTrigger) {
				activeTrigger.focus();
				activeTrigger = null;
			}
		};

		document.addEventListener("click", (event) => {
			const trigger = event.target.closest("[data-social-proof-open]");
			if (!(trigger instanceof HTMLElement)) return;

			if (modalName) modalName.textContent = trigger.dataset.name || "";
			if (modalTitle) modalTitle.textContent = trigger.dataset.title || "";
			if (modalQuote) modalQuote.textContent = trigger.dataset.quote || "";

			activeTrigger = trigger;
			socialProofModal.removeAttribute("hidden");
			socialProofModal.setAttribute("aria-hidden", "false");
			document.body.classList.add("landing12-no-scroll");
			if (closeButton) closeButton.focus();
		});

		modalCloseControls.forEach((control) => {
			control.addEventListener("click", closeSocialProofModal);
		});

		window.addEventListener("keydown", (event) => {
			if (event.key === "Escape" && !socialProofModal.hasAttribute("hidden")) {
				closeSocialProofModal();
			}
		});
	}

	const trailerModal = document.querySelector("[data-trailer-modal]");
	if (trailerModal) {
		document.body.appendChild(trailerModal);

		const trailerIframe = trailerModal.querySelector("[data-trailer-iframe]");
		const trailerModalTitle = trailerModal.querySelector("[data-trailer-modal-title]");
		const trailerCloseControls = trailerModal.querySelectorAll("[data-trailer-close]");
		const trailerCloseButton = trailerModal.querySelector(".landing12-trailer-modal__close");
		let activeTrailerTrigger = null;

		const closeTrailerModal = () => {
			if (trailerIframe instanceof HTMLIFrameElement) {
				trailerIframe.src = "";
			}
			trailerModal.setAttribute("hidden", "");
			trailerModal.setAttribute("aria-hidden", "true");
			document.body.classList.remove("landing12-no-scroll");
			if (activeTrailerTrigger) {
				activeTrailerTrigger.focus();
				activeTrailerTrigger = null;
			}
		};

		document.addEventListener("click", (event) => {
			const trigger = event.target.closest("[data-trailer-open]");
			if (!(trigger instanceof HTMLElement)) return;

			const videoIdRaw = trigger.dataset.videoId || "";
			const videoId = /^[a-zA-Z0-9_-]{6,}$/.test(videoIdRaw) ? videoIdRaw : "";
			if (!videoId) return;

			if (trailerModalTitle) {
				trailerModalTitle.textContent = trigger.dataset.title || "Video";
			}

			if (trailerIframe instanceof HTMLIFrameElement) {
				const embedUrl = `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`;
				trailerIframe.src = embedUrl;
			}

			activeTrailerTrigger = trigger;
			trailerModal.removeAttribute("hidden");
			trailerModal.setAttribute("aria-hidden", "false");
			document.body.classList.add("landing12-no-scroll");
			if (trailerCloseButton instanceof HTMLElement) trailerCloseButton.focus();
		});

		trailerCloseControls.forEach((control) => {
			control.addEventListener("click", closeTrailerModal);
		});

		window.addEventListener("keydown", (event) => {
			if (event.key === "Escape" && !trailerModal.hasAttribute("hidden")) {
				closeTrailerModal();
			}
		});
	}

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
