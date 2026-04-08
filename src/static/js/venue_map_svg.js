/**
 * venue_map_svg.js
 * Interactivity for the SVG icon-style venue diagram of The Gorge Amphitheatre.
 */

(function () {
	"use strict";

	// ── POI data ──────────────────────────────────────────────────────────────
	const POIS = {
		"main-stage": {
			name: "Main Stage",
			category: "Stage",
			icon: "🎵",
			description:
				"The legendary main stage overlooking the Columbia River Gorge — one of the most scenic concert venues on the planet. FreedomCon performances run across three days on this iconic stage.",
		},
		"seating-inner": {
			name: "Reserved Seating — Rows A–C",
			category: "Stage / Seating",
			icon: "💺",
			description:
				"The closest reserved seats to the stage. Front-row energy with numbered, assigned seating. Included with Reserved A–C ticket tier.",
		},
		"seating-mid": {
			name: "Reserved Seating — Rows D–F",
			category: "Stage / Seating",
			icon: "💺",
			description:
				"Mid-section reserved seating with excellent sightlines and easy concourse access. Included with Reserved D–F ticket tier.",
		},
		"seating-outer": {
			name: "Reserved Seating — Rows G–H",
			category: "Stage / Seating",
			icon: "💺",
			description:
				"Back reserved rows with sweeping views of the stage and the gorge. Great for groups. Included with Reserved G–H ticket tier.",
		},
		lawn: {
			name: "General Lawn",
			category: "Stage / Seating",
			icon: "🌿",
			description:
				"The open-air general admission lawn is the heart of the festival — blankets, dancing, and canyon views as far as the eye can see. Included with General Admission tickets.",
		},
		"main-entrance": {
			name: "Main Entrance / Box Office",
			category: "Entrance",
			icon: "🚪",
			description:
				"Primary entry point for all ticket holders. Will-call and box office are located here. Gates open 2 hours before the first performance.",
		},
		"ada-entrance": {
			name: "ADA Accessible Entrance",
			category: "Entrance",
			icon: "♿",
			description:
				"Dedicated accessible entry with level pathways, companion seating, and priority access. Please notify staff if you need assistance.",
		},
		"exit-gate": {
			name: "Exit Gate",
			category: "Entrance",
			icon: "🔚",
			description:
				"Designated exit-only gate for post-show egress. Re-entry with valid wristband is available at the Main Entrance.",
		},
		"parking-north": {
			name: "North Parking Lots",
			category: "Parking",
			icon: "🅿️",
			description:
				"Main general-admission parking. Lots open 3 hours before doors. General parking is included with most ticket packages; space is first-come, first-served.",
		},
		"parking-vip": {
			name: "VIP Parking",
			category: "Parking",
			icon: "⭐",
			description:
				"Reserved VIP and accessible parking near the main entrance. A valid VIP parking permit is required — available as an add-on at checkout.",
		},
		"parking-south": {
			name: "South Parking Lots",
			category: "Parking",
			icon: "🅿️",
			description:
				"Overflow parking with a free shuttle service running every 15 minutes to the main entrance. Great option if north lots are full.",
		},
		"camping-gorge": {
			name: "Gorge Campground",
			category: "Camping",
			icon: "⛺",
			description:
				"Official on-site festival camping with fire pits, shared restrooms, and outdoor showers. Walk straight from your tent to the show. Camping passes available separately.",
		},
		"food-court": {
			name: "Food & Beverage Court",
			category: "Amenity",
			icon: "🍔",
			description:
				"Multiple local and regional food vendors plus full bar service. Non-alcoholic and vegetarian options available throughout the concourse. Open from gate time through last set.",
		},
		merch: {
			name: "Merchandise Booth",
			category: "Amenity",
			icon: "👕",
			description:
				"Official FreedomCon merchandise including limited-edition apparel, posters, and artist merch. Pre-order online to skip the line — pick up at the booth on arrival.",
		},
		"first-aid": {
			name: "First Aid / Medical",
			category: "Amenity",
			icon: "🏥",
			description:
				"Fully staffed medical station open from doors through 1 hour after the final performance. For emergencies, locate any staff member in a yellow vest.",
		},
		restrooms: {
			name: "Restrooms",
			category: "Amenity",
			icon: "🚻",
			description:
				"Permanent restroom facilities and additional portable units positioned throughout the concourse. ADA-accessible units are located near all entrances.",
		},
		"info-booth": {
			name: "Information Booth",
			category: "Amenity",
			icon: "ℹ️",
			description:
				"Staff on hand for schedules, lost & found, wristband questions, accessibility requests, and general festival information.",
		},
	};

	// ── DOM references ────────────────────────────────────────────────────────
	const svgEl   = document.getElementById("venue-svg-map");
	const panel   = document.getElementById("vm-panel");
	const panelIcon = document.getElementById("vm-panel-icon");
	const panelCat  = document.getElementById("vm-panel-cat");
	const panelName = document.getElementById("vm-panel-name");
	const panelDesc = document.getElementById("vm-panel-desc");
	const closeBtn  = document.getElementById("vm-panel-close");

	// ── Active zone tracking ─────────────────────────────────────────────────
	let activePoiId = null;

	// ── Open info panel ───────────────────────────────────────────────────────
	function openPanel(poiId) {
		const poi = POIS[poiId];
		if (!poi) return;

		panelIcon.textContent = poi.icon;
		panelCat.textContent  = poi.category;
		panelName.textContent = poi.name;
		panelDesc.textContent = poi.description;

		panel.removeAttribute("hidden");

		// Highlight the active zone
		document.querySelectorAll(".vm-zone").forEach(function (el) {
			el.classList.remove("vm-active");
		});
		document.querySelectorAll('[data-poi="' + poiId + '"]').forEach(function (el) {
			el.classList.add("vm-active");
		});

		activePoiId = poiId;
	}

	// ── Close info panel ──────────────────────────────────────────────────────
	function closePanel() {
		panel.setAttribute("hidden", "");
		document.querySelectorAll(".vm-zone").forEach(function (el) {
			el.classList.remove("vm-active");
		});
		activePoiId = null;
	}

	// ── Wire zone clicks ──────────────────────────────────────────────────────
	svgEl.querySelectorAll(".vm-zone").forEach(function (zone) {
		zone.addEventListener("click", function () {
			const id = zone.dataset.poi;
			if (!id) return;
			if (id === activePoiId) {
				closePanel();
			} else {
				openPanel(id);
			}
		});

		// Keyboard accessibility
		zone.setAttribute("tabindex", "0");
		zone.setAttribute("role", "button");
		zone.addEventListener("keydown", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				zone.click();
			}
		});
	});

	closeBtn.addEventListener("click", closePanel);

	// Close on Escape
	document.addEventListener("keydown", function (e) {
		if (e.key === "Escape" && activePoiId) closePanel();
	});

	// ── Filter logic ──────────────────────────────────────────────────────────
	function applyFilter(cat) {
		document.querySelectorAll(".vm-zone").forEach(function (zone) {
			const zoneCat = zone.dataset.cat || "";
			if (cat === "all" || zoneCat === cat) {
				zone.classList.remove("vm-faded");
			} else {
				zone.classList.add("vm-faded");
				// Close panel if active zone is being hidden
				if (zone.dataset.poi === activePoiId) closePanel();
			}
		});
	}

	document.querySelectorAll(".vm-filter-btn").forEach(function (btn) {
		btn.addEventListener("click", function () {
			document.querySelectorAll(".vm-filter-btn").forEach(function (b) {
				b.classList.remove("vm-filter-btn--active");
			});
			btn.classList.add("vm-filter-btn--active");
			applyFilter(btn.dataset.cat);
		});
	});
})();
