/**
 * venue_map.js
 * Interactive Leaflet map of The Gorge Amphitheatre, George, WA.
 */

(function () {
	"use strict";

	// ── Points of Interest ────────────────────────────────────────────────────
	const POIS = [
		{
			id: "main-stage",
			name: "Main Stage",
			category: "stage",
			icon: "🎵",
			lat: 46.87395,
			lng: -119.98505,
			description: "The legendary main stage overlooking the Columbia River Gorge.",
		},
		{
			id: "main-entrance",
			name: "Main Entrance / Box Office",
			category: "entrance",
			icon: "🚪",
			lat: 46.87535,
			lng: -119.98420,
			description: "Primary entry point and will-call ticket pickup.",
		},
		{
			id: "ada-entrance",
			name: "ADA Accessible Entrance",
			category: "entrance",
			icon: "♿",
			lat: 46.87490,
			lng: -119.98460,
			description: "Accessible entry with level pathways to the venue.",
		},
		{
			id: "lawn-general",
			name: "General Lawn Seating",
			category: "stage",
			icon: "🌿",
			lat: 46.87355,
			lng: -119.98480,
			description: "Open lawn area with spectacular canyon and river views.",
		},
		{
			id: "reserved-seating",
			name: "Reserved Seating (Sections A–H)",
			category: "stage",
			icon: "💺",
			lat: 46.87375,
			lng: -119.98510,
			description: "Numbered reserved seats closest to the stage.",
		},
		{
			id: "parking-north",
			name: "North Parking Lot",
			category: "parking",
			icon: "🅿️",
			lat: 46.87640,
			lng: -119.98400,
			description: "Main general parking area. Opens 3 hours before doors.",
		},
		{
			id: "parking-south",
			name: "South Parking Lot",
			category: "parking",
			icon: "🅿️",
			lat: 46.87240,
			lng: -119.98460,
			description: "Overflow parking; free shuttle service to the entrance.",
		},
		{
			id: "parking-vip",
			name: "VIP Parking",
			category: "parking",
			icon: "⭐",
			lat: 46.87580,
			lng: -119.98340,
			description: "Reserved VIP and accessible parking — permit required.",
		},
		{
			id: "camping-gorge",
			name: "Gorge Campground",
			category: "camping",
			icon: "⛺",
			lat: 46.87160,
			lng: -119.98530,
			description: "On-site festival camping with fire pits and shared restrooms.",
		},
		{
			id: "camping-rv",
			name: "RV / Car Camping",
			category: "camping",
			icon: "🚐",
			lat: 46.87100,
			lng: -119.98400,
			description: "RV hook-ups and car-camping spots near the south lot.",
		},
		{
			id: "food-court",
			name: "Food & Beverage Court",
			category: "amenity",
			icon: "🍔",
			lat: 46.87460,
			lng: -119.98490,
			description: "Multiple food vendors, bars, and non-alcoholic options.",
		},
		{
			id: "merch",
			name: "Merchandise Booth",
			category: "amenity",
			icon: "👕",
			lat: 46.87505,
			lng: -119.98430,
			description: "Official FreedomCon merchandise and artist merch.",
		},
		{
			id: "first-aid",
			name: "First Aid / Medical",
			category: "amenity",
			icon: "🏥",
			lat: 46.87515,
			lng: -119.98390,
			description: "Staffed medical station open throughout the event.",
		},
		{
			id: "restrooms",
			name: "Restrooms",
			category: "amenity",
			icon: "🚻",
			lat: 46.87435,
			lng: -119.98510,
			description: "Permanent and portable restroom facilities.",
		},
		{
			id: "info-booth",
			name: "Information Booth",
			category: "amenity",
			icon: "ℹ️",
			lat: 46.87525,
			lng: -119.98450,
			description: "Staff on hand for schedules, lost & found, and general help.",
		},
	];

	// ── Category color map (read from CSS custom properties) ────────────────
	const rootStyle = getComputedStyle(document.documentElement);
	function cssVar(name) {
		return rootStyle.getPropertyValue(name).trim();
	}
	const CAT_COLOR = {
		stage:    cssVar("--venue-color-stage"),
		entrance: cssVar("--venue-color-entrance"),
		parking:  cssVar("--venue-color-parking"),
		camping:  cssVar("--venue-color-camping"),
		amenity:  cssVar("--venue-color-amenity"),
	};

	// ── State ─────────────────────────────────────────────────────────────────
	let activeCategory = "all";
	const markersByPoi = {}; // id → Leaflet marker
	const listItemsByPoi = {}; // id → <li> element

	// ── Initialise map ────────────────────────────────────────────────────────
	const map = L.map("venue-map", {
		center: [46.8738, -119.9848],
		zoom: 16,
		zoomControl: true,
		scrollWheelZoom: true,
	});

	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		maxZoom: 19,
		attribution:
			'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	}).addTo(map);

	// ── Helper: create a coloured div icon ───────────────────────────────────
	function createIcon(poi) {
		const color = CAT_COLOR[poi.category] || "#333";
		return L.divIcon({
			className: "",
			html: `<div class="venue-map-marker venue-map-marker--${poi.category}" style="background:${color};" title="${poi.name}">${poi.icon}</div>`,
			iconSize: [32, 32],
			iconAnchor: [16, 16],
			popupAnchor: [0, -18],
		});
	}

	// ── Helper: build popup HTML ──────────────────────────────────────────────
	function popupHtml(poi) {
		return `<b>${poi.name}</b><br><span style="color:${CAT_COLOR[poi.category]};font-size:0.8em;text-transform:uppercase;letter-spacing:.06em">${poi.category}</span><br><span style="font-size:.9em">${poi.description}</span>`;
	}

	// ── Build markers + sidebar list ─────────────────────────────────────────
	const listEl = document.getElementById("poi-list-items");

	POIS.forEach(function (poi) {
		// Marker
		const marker = L.marker([poi.lat, poi.lng], { icon: createIcon(poi) })
			.addTo(map)
			.bindPopup(popupHtml(poi));
		markersByPoi[poi.id] = marker;

		// List item
		const li = document.createElement("li");
		li.className = "venue-map-poi-list__item";
		li.dataset.id = poi.id;
		li.dataset.category = poi.category;
		li.innerHTML = `
			<p class="venue-map-poi-list__item-name">${poi.icon} ${poi.name}</p>
			<p class="venue-map-poi-list__item-cat">${poi.category}</p>
			<p class="venue-map-poi-list__item-desc">${poi.description}</p>
		`;
		li.addEventListener("click", function () {
			map.setView([poi.lat, poi.lng], 17, { animate: true });
			marker.openPopup();
		});
		listEl.appendChild(li);
		listItemsByPoi[poi.id] = li;
	});

	// ── Filter logic ──────────────────────────────────────────────────────────
	function applyFilter(category) {
		activeCategory = category;

		POIS.forEach(function (poi) {
			const visible = category === "all" || poi.category === category;
			const marker = markersByPoi[poi.id];
			const li = listItemsByPoi[poi.id];

			if (visible) {
				if (!map.hasLayer(marker)) map.addLayer(marker);
				li.style.display = "";
			} else {
				if (map.hasLayer(marker)) map.removeLayer(marker);
				li.style.display = "none";
			}
		});
	}

	// ── Wire up filter buttons ────────────────────────────────────────────────
	document.querySelectorAll(".venue-map-filter-btn").forEach(function (btn) {
		btn.addEventListener("click", function () {
			document.querySelectorAll(".venue-map-filter-btn").forEach(function (b) {
				b.classList.remove("venue-map-filter-btn--active");
			});
			btn.classList.add("venue-map-filter-btn--active");
			applyFilter(btn.dataset.category);
		});
	});
})();
