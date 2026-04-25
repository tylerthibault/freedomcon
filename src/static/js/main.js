document.addEventListener("DOMContentLoaded", () => {
	console.log("SIteCoded landing page loaded.");

	const landing12Nav = document.querySelector(".landing12-nav");
	if (landing12Nav) {
		const mobileNavQuery = window.matchMedia("(max-width: 760px)");
		let landing12LastScrollY = window.scrollY;
		let landing12ScrollTicking = false;

		const syncLanding12MobileNavState = () => {
			landing12ScrollTicking = false;

			const currentScrollY = Math.max(window.scrollY, 0);
			const isAtTop = currentScrollY <= 24;
			const nearBottom = (currentScrollY + window.innerHeight) >= (document.documentElement.scrollHeight - 80);
			landing12Nav.classList.toggle("is-at-top", isAtTop);

			if (mobileNavQuery.matches) {
				// Mobile: always condensed once past the top
				if (isAtTop) {
					landing12Nav.classList.add("is-condensed");
				} else {
					landing12Nav.classList.add("is-condensed");
				}
				landing12LastScrollY = currentScrollY;
				return;
			} else {
				// Desktop: full size at top, shrink when scrolling down
				if (isAtTop) {
					landing12Nav.classList.remove("is-condensed");
					landing12LastScrollY = currentScrollY;
					return;
				}
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

		// Keep --nav-height in sync with actual header height for fixed-nav offset
		const landing12Header = landing12Nav.closest('.landing12-header');
		const updateNavHeight = () => {
			if (landing12Header) {
				document.documentElement.style.setProperty('--nav-height', landing12Header.offsetHeight + 'px');
			}
		};
		updateNavHeight();
		window.addEventListener('resize', updateNavHeight);

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

		const isMobile = window.matchMedia("(max-width: 767px)").matches;

		const observer = new IntersectionObserver((entries, instance) => {
			entries.forEach((entry) => {
				if (!entry.isIntersecting) return;
				entry.target.classList.add("is-revealed");
				instance.unobserve(entry.target);
			});
		}, {
			root: null,
			rootMargin: isMobile ? "0px 0px -22% 0px" : "0px 0px -10% 0px",
			threshold: 0,
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

	const mediaSections = document.querySelectorAll("[data-media-section]");
	mediaSections.forEach((section) => {
		const cards = Array.from(section.querySelectorAll("[data-media-item]"));
		const toggle = section.querySelector("[data-media-toggle]");

		if (!cards.length || !(toggle instanceof HTMLButtonElement)) {
			return;
		}

		const totalCards = cards.length;
		const initialCount = Math.max(0, Number(section.dataset.initialCount || 4));
		const revealCount = Math.max(0, Number(section.dataset.revealCount || 6));
		const showMoreLabel = toggle.dataset.showMoreLabel || "Show More";
		const showAllLabel = toggle.dataset.showAllLabel || "Show All";

		let visibleCount = Math.min(totalCards, initialCount);
		let hasRevealedMore = false;

		const syncMediaGrid = () => {
			cards.forEach((card, index) => {
				const isVisible = index < visibleCount;
				card.hidden = !isVisible;
				card.toggleAttribute("data-media-hidden", !isVisible);
			});

			const remainingCount = totalCards - visibleCount;
			if (remainingCount <= 0) {
				toggle.hidden = true;
				toggle.setAttribute("aria-expanded", "true");
				return;
			}

			toggle.hidden = false;
			toggle.textContent = hasRevealedMore ? showAllLabel : showMoreLabel;
			toggle.setAttribute("aria-expanded", visibleCount >= totalCards ? "true" : "false");
		};

		syncMediaGrid();

		toggle.addEventListener("click", () => {
			if (!hasRevealedMore) {
				visibleCount = Math.min(totalCards, initialCount + revealCount);
				hasRevealedMore = true;
				syncMediaGrid();
				return;
			}

			visibleCount = totalCards;
			syncMediaGrid();
		});
	});

	// ── Skeleton loading boxes for <details> conference panels ──
	document.querySelectorAll(".about-smn-conference__panel").forEach((details) => {
		if (!(details instanceof HTMLDetailsElement)) return;

		details.addEventListener("toggle", () => {
			if (!details.open) return;

			details.querySelectorAll("[data-youtube-thumb]").forEach((img) => {
				if (!(img instanceof HTMLImageElement)) return;
				if (img.complete && img.naturalWidth > 0) return; // already cached

				const card = img.closest(".landing12-trailer-card");
				if (!card) return;

				card.classList.add("is-loading");

				const done = () => card.classList.remove("is-loading");
				img.addEventListener("load",  done, { once: true });
				img.addEventListener("error", done, { once: true });
			});
		});
	});

	document.querySelectorAll("[data-youtube-thumb]").forEach((image) => {
		if (!(image instanceof HTMLImageElement)) {
			return;
		}

		const handleThumbnailError = () => {
			const fallbackSrc = image.dataset.thumbFallback || "";
			const finalSrc = image.dataset.thumbFinal || "";
			const stage = image.dataset.thumbStage || "primary";

			if (stage === "primary" && fallbackSrc && image.src !== fallbackSrc) {
				image.dataset.thumbStage = "fallback";
				image.src = fallbackSrc;
				return;
			}

			if (stage !== "final" && finalSrc && image.src !== finalSrc) {
				image.dataset.thumbStage = "final";
				image.src = finalSrc;
				return;
			}

			image.removeEventListener("error", handleThumbnailError);
		};

		image.addEventListener("error", handleThumbnailError);
	});

	const mediaModal = document.querySelector("[data-media-modal]");
	if (mediaModal) {
		document.body.appendChild(mediaModal);

		const mediaIframe = mediaModal.querySelector("[data-media-iframe]");
		const mediaModalTitle = mediaModal.querySelector("[data-media-modal-title]");
		const mediaCloseControls = mediaModal.querySelectorAll("[data-media-close]");
		const mediaCloseButton = mediaModal.querySelector(".landing12-trailer-modal__close");
		let activeMediaTrigger = null;

		const closeMediaModal = () => {
			if (mediaIframe instanceof HTMLIFrameElement) {
				mediaIframe.src = "";
			}
			mediaModal.setAttribute("hidden", "");
			mediaModal.setAttribute("aria-hidden", "true");
			document.body.classList.remove("landing12-no-scroll");
			if (activeMediaTrigger) {
				activeMediaTrigger.focus();
				activeMediaTrigger = null;
			}
		};

		document.addEventListener("click", (event) => {
			const trigger = event.target.closest("[data-media-open]");
			if (!(trigger instanceof HTMLElement)) return;

			const videoIdRaw = trigger.dataset.videoId || "";
			const videoId = /^[a-zA-Z0-9_-]{6,}$/.test(videoIdRaw) ? videoIdRaw : "";
			if (!videoId) return;

			if (mediaModalTitle) {
				mediaModalTitle.textContent = trigger.dataset.title || "Video";
			}

			if (mediaIframe instanceof HTMLIFrameElement) {
				mediaIframe.src = `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`;
			}

			activeMediaTrigger = trigger;
			mediaModal.removeAttribute("hidden");
			mediaModal.setAttribute("aria-hidden", "false");
			document.body.classList.add("landing12-no-scroll");
			if (mediaCloseButton instanceof HTMLElement) mediaCloseButton.focus();
		});

		mediaCloseControls.forEach((control) => {
			control.addEventListener("click", closeMediaModal);
		});

		window.addEventListener("keydown", (event) => {
			if (event.key === "Escape" && !mediaModal.hasAttribute("hidden")) {
				closeMediaModal();
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

/* =================================================================
   Speaker Bio Modal — global, works on every page
   ================================================================= */
(function () {
	var backdrop = document.getElementById('speakerBioModal');
	if (!backdrop) return;

	var closeBtn  = document.getElementById('sbmClose');
	var sbmImg    = backdrop.querySelector('[data-sbm-img]');
	var sbmName   = backdrop.querySelector('[data-sbm-name]');
	var sbmTitles = backdrop.querySelector('[data-sbm-titles]');
	var sbmBio    = backdrop.querySelector('[data-sbm-bio]');
	var sbmOrgs   = backdrop.querySelector('[data-sbm-orgs]');
	var sbmRight  = backdrop.querySelector('.spk-modal__right');
	var sbmLeft   = backdrop.querySelector('[data-sbm-left]');

	var ICONS = {
		church:  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2 3h3l-1.5 2H17v2l-5 3-5-3V7h1.5L7 5h3L12 2zm-5 9v10h4v-4h2v4h4V11l-5-3-5 3z"/></svg>',
		shield:  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L3 6v6c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V6l-9-4z"/></svg>',
		book:    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M18 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/></svg>',
		mic:     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3zm-7 11a7 7 0 0014 0h-2a5 5 0 01-10 0H5zm7 7v3h-2v-3a9 9 0 01-2-.37v-2.1a7 7 0 004 .47 7 7 0 004-.47v2.1A9 9 0 0119 21v-2z"/></svg>',
		star:    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
		cap:     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3zm0 13L3 11.2V16c0 3.31 4.03 6 9 6s9-2.69 9-6v-4.8L12 16z"/></svg>',
		podcast: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a7 7 0 00-7 7c0 1.79.66 3.42 1.74 4.67l1.46-1.46A4.96 4.96 0 017 9a5 5 0 0110 0c0 1.28-.49 2.45-1.29 3.34l1.42 1.42A6.96 6.96 0 0019 9a7 7 0 00-7-7zm0 4a3 3 0 00-3 3c0 .78.3 1.5.78 2.04l1.45-1.45A1 1 0 0111 9a1 1 0 112 0 1 1 0 01-.23.59l1.45 1.45C14.7 10.5 15 9.78 15 9a3 3 0 00-3-3zm-1 8h2v7h-2v-7zm-3 3h2v4H8v-4zm6 0h2v4h-2v-4z"/></svg>',
		flag:    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6h-5.6z"/></svg>'
	};

	function openModal(card) {
		var name = card.dataset.name || '';
		var img  = card.dataset.img  || '';
		var alt  = card.dataset.alt  || name;
		var bio  = card.dataset.bio  || '';
		var titles = [], orgs = [];
		try { titles = JSON.parse(card.dataset.titles || '[]'); } catch (e) {}
		try { orgs   = JSON.parse(card.dataset.orgs   || '[]'); } catch (e) {}

		sbmImg.src = img;
		sbmImg.alt = alt;
		if (sbmLeft) sbmLeft.style.setProperty('--sbm-bg-img', 'url(' + img + ')');
		sbmName.textContent = name;
		sbmTitles.textContent = titles.filter(Boolean).join('  |  ');

		sbmBio.innerHTML = bio
			.split('\n')
			.map(function(p) { return p.trim(); })
			.filter(Boolean)
			.map(function(p) { return '<p>' + p + '</p>'; })
			.join('');

		sbmOrgs.innerHTML = orgs.map(function(org) {
			return [
				'<li class="spk-modal__org-row">',
					'<span class="spk-modal__org-icon">' + (ICONS[org.icon] || '') + '</span>',
					'<span class="spk-modal__org-info">',
						'<strong>' + org.name + '</strong>',
						'<small>' + org.subtitle + '</small>',
					'</span>',
				'</li>'
			].join('');
		}).join('');

		backdrop.setAttribute('aria-hidden', 'false');
		backdrop.classList.add('spk-modal-backdrop--open');
		document.body.classList.add('spk-modal-open');
		if (sbmRight) sbmRight.scrollTop = 0;
		backdrop.scrollTop = 0;
		closeBtn.focus();
	}

	function closeModal() {
		backdrop.setAttribute('aria-hidden', 'true');
		backdrop.classList.remove('spk-modal-backdrop--open');
		document.body.classList.remove('spk-modal-open');
	}

	document.querySelectorAll('[data-speaker-open]').forEach(function(card) {
		card.addEventListener('click', function() { openModal(card); });
		card.addEventListener('keydown', function(e) {
			if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(card); }
		});
	});

	closeBtn.addEventListener('click', closeModal);
	backdrop.addEventListener('click', function(e) { if (e.target === backdrop) closeModal(); });
	document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });
}());
