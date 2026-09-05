const STORAGE_KEYS = {
  favorites: "adamsy-free-tv:favorites",
  history: "adamsy-free-tv:history",
  adminToken: "adamsy-free-tv:admin-token",
};

const HLS_SCRIPT_URL = "https://cdn.jsdelivr.net/npm/hls.js@1";
const CHANNELS_PER_PAGE = 48;

const state = {
  items: [],
  categories: [],
  countries: [],
  selectedChannel: null,
  favorites: new Set(),
  history: [],
  refreshState: null,
  hls: null,
  hlsLoadAttempted: false,
  activeCategory: "All",
  activeView: "all",
  page: 1,
  deferredInstallPrompt: null,
};

const elements = {
  apiStatus: document.querySelector("#api-status"),
  sourceMeta: document.querySelector("#source-meta"),
  visibleCount: document.querySelector("#visible-count"),
  totalCount: document.querySelector("#total-count"),
  categoryCount: document.querySelector("#category-count"),
  countryCount: document.querySelector("#country-count"),
  favoriteCount: document.querySelector("#favorite-count"),
  recentCount: document.querySelector("#recent-count"),
  categoryChips: document.querySelector("#category-chips"),
  countrySelect: document.querySelector("#country-select"),
  viewTabs: document.querySelector("#view-tabs"),
  searchInput: document.querySelector("#search-input"),
  reloadButton: document.querySelector("#reload-button"),
  syncButton: document.querySelector("#sync-button"),
  installButton: document.querySelector("#install-button"),
  settingsButton: document.querySelector("#settings-button"),
  adminPanel: document.querySelector("#admin-panel"),
  resetFilters: document.querySelector("#reset-filters"),
  favoritesOnlyButton: document.querySelector("#favorites-only-button"),
  recentOnlyButton: document.querySelector("#recent-only-button"),
  verifyLiveCheckbox: document.querySelector("#verify-live-checkbox"),
  adminTokenInput: document.querySelector("#admin-token-input"),
  refreshStatusText: document.querySelector("#refresh-status-text"),
  resultsCaption: document.querySelector("#results-caption"),
  channelGrid: document.querySelector("#channel-grid"),
  emptyState: document.querySelector("#empty-state"),
  favoritesStrip: document.querySelector("#favorites-strip"),
  recentStrip: document.querySelector("#recent-strip"),
  paginationPrev: document.querySelector("#pagination-prev"),
  paginationNext: document.querySelector("#pagination-next"),
  paginationIndicator: document.querySelector("#pagination-indicator"),
  playerFrame: document.querySelector("#player-frame"),
  player: document.querySelector("#channel-player"),
  playerPlaceholder: document.querySelector("#player-placeholder"),
  playerLoading: document.querySelector("#player-loading"),
  playerMode: document.querySelector("#player-mode"),
  fullscreenButton: document.querySelector("#fullscreen-button"),
  pipButton: document.querySelector("#pip-button"),
  currentChannelName: document.querySelector("#current-channel-name"),
  currentChannelMeta: document.querySelector("#current-channel-meta"),
  favoriteButton: document.querySelector("#favorite-button"),
  openStreamLink: document.querySelector("#open-stream-link"),
  copyStreamButton: document.querySelector("#copy-stream-button"),
};

function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), delay);
  };
}

function readStoredJson(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    console.error(error);
    return fallback;
  }
}

function saveStoredJson(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

function loadStoredState() {
  state.favorites = new Set(readStoredJson(STORAGE_KEYS.favorites, []));
  state.history = readStoredJson(STORAGE_KEYS.history, []);
  elements.adminTokenInput.value = window.localStorage.getItem(STORAGE_KEYS.adminToken) || "";
}

function persistFavorites() {
  saveStoredJson(STORAGE_KEYS.favorites, Array.from(state.favorites));
}

function persistHistory() {
  saveStoredJson(STORAGE_KEYS.history, state.history.slice(0, 12));
}

function persistAdminToken() {
  window.localStorage.setItem(STORAGE_KEYS.adminToken, elements.adminTokenInput.value.trim());
}

function setApiStatus(label, ok = true) {
  elements.apiStatus.textContent = label;
  elements.apiStatus.classList.toggle("error", !ok);
}

function setPlayerMode(label, ok = true) {
  elements.playerMode.textContent = label;
  elements.playerMode.classList.toggle("error", !ok);
}

function getRequestHeaders() {
  const headers = {
    Accept: "application/json",
  };
  const token = elements.adminTokenInput.value.trim();
  if (token) {
    headers["x-admin-token"] = token;
  }
  return headers;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...getRequestHeaders(),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const error = new Error(`Request failed: ${response.status}`);
    error.status = response.status;
    try {
      error.payload = await response.json();
    } catch {
      error.payload = null;
    }
    throw error;
  }

  return response.json();
}

function populateSelect(select, items) {
  const currentValue = select.value || "All";
  select.innerHTML = "";

  const allOption = document.createElement("option");
  allOption.value = "All";
  allOption.textContent = "All";
  select.appendChild(allOption);

  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item;
    select.appendChild(option);
  });

  select.value = items.includes(currentValue) || currentValue === "All" ? currentValue : "All";
}

function setActiveCategory(category) {
  state.activeCategory = category;
  state.page = 1;
  renderCategoryChips();
  renderFromState();
}

const QUICK_CATEGORY_CHIP_LIMIT = 14;

function getCategoryCounts() {
  const counts = new Map();
  state.items.forEach((channel) => {
    if (!channel.category) {
      return;
    }
    counts.set(channel.category, (counts.get(channel.category) || 0) + 1);
  });
  return counts;
}

function renderCategoryChips() {
  elements.categoryChips.innerHTML = "";

  // iptv-org's category labels are inconsistent enough that some catalogs
  // carry 150+ distinct values - showing them all as chips would be worse
  // than the dropdown it replaced. Surface the most common ones as quick
  // buttons and tuck the long tail into a small overflow select instead.
  const counts = getCategoryCounts();
  const sortedByCount = [...state.categories].sort((a, b) => (counts.get(b) || 0) - (counts.get(a) || 0));
  const quickCategories = sortedByCount.slice(0, QUICK_CATEGORY_CHIP_LIMIT);

  if (state.activeCategory !== "All" && !quickCategories.includes(state.activeCategory)) {
    quickCategories.push(state.activeCategory);
  }

  ["All", ...quickCategories].forEach((category) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip-button";
    chip.textContent = category;
    chip.setAttribute("role", "tab");
    chip.setAttribute("aria-selected", String(category === state.activeCategory));
    if (category === state.activeCategory) {
      chip.classList.add("active");
    }
    chip.addEventListener("click", () => setActiveCategory(category));
    elements.categoryChips.appendChild(chip);
  });

  const overflowCategories = sortedByCount
    .filter((category) => !quickCategories.includes(category))
    .sort((a, b) => a.localeCompare(b));

  if (overflowCategories.length > 0) {
    const overflowSelect = document.createElement("select");
    overflowSelect.className = "chip-overflow-select";
    overflowSelect.setAttribute("aria-label", "More categories");

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = `More categories (${overflowCategories.length})…`;
    overflowSelect.appendChild(placeholder);

    overflowCategories.forEach((category) => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = category;
      if (category === state.activeCategory) {
        option.selected = true;
      }
      overflowSelect.appendChild(option);
    });

    overflowSelect.addEventListener("change", () => {
      if (overflowSelect.value) {
        setActiveCategory(overflowSelect.value);
      }
    });

    elements.categoryChips.appendChild(overflowSelect);
  }
}

function setActiveView(view) {
  state.activeView = view;
  state.page = 1;
  updateViewTabs();
  renderFromState();
}

function updateViewTabs() {
  elements.viewTabs.querySelectorAll(".segmented-button").forEach((button) => {
    const isActive = button.dataset.view === state.activeView;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

function formatMeta(channel) {
  const parts = [];
  if (channel.country) {
    parts.push(channel.country);
  }
  if (channel.category) {
    parts.push(channel.category);
  }
  return parts.length ? parts.join(" | ") : "Uncategorized stream";
}

function isFavorite(channel) {
  return state.favorites.has(channel.url);
}

function sanitizeRecentItems(items) {
  const seen = new Set();
  return items.filter((item) => {
    if (!item?.url || seen.has(item.url)) {
      return false;
    }
    seen.add(item.url);
    return true;
  });
}

function rememberChannel(channel) {
  state.history = sanitizeRecentItems([
    {
      name: channel.name,
      url: channel.url,
      country: channel.country,
      category: channel.category,
    },
    ...state.history.filter((item) => item.url !== channel.url),
  ]).slice(0, 12);
  persistHistory();
}

function findChannelByUrl(url) {
  return state.items.find((item) => item.url === url) || state.history.find((item) => item.url === url) || null;
}

function renderStats(totalVisible) {
  elements.visibleCount.textContent = String(totalVisible);
  elements.totalCount.textContent = String(state.items.length);
  elements.categoryCount.textContent = String(state.categories.length);
  elements.countryCount.textContent = String(state.countries.length);
  elements.favoriteCount.textContent = String(state.favorites.size);
  elements.recentCount.textContent = String(state.history.length);
}

function renderSavedStrip(target, items, emptyMessage) {
  target.innerHTML = "";

  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "saved-empty";
    empty.textContent = emptyMessage;
    target.appendChild(empty);
    return;
  }

  items.forEach((channel) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "saved-chip";
    if (state.selectedChannel?.url === channel.url) {
      button.classList.add("active");
    }
    button.innerHTML = `<strong>${channel.name}</strong><span>${formatMeta(channel)}</span>`;
    button.addEventListener("click", () => activatePlayer(channel));
    target.appendChild(button);
  });
}

function getFavoriteChannels() {
  return state.items.filter((channel) => isFavorite(channel));
}

function getRecentChannels() {
  return sanitizeRecentItems(state.history.map((item) => findChannelByUrl(item.url) || item));
}

function renderSavedCollections() {
  renderSavedStrip(elements.favoritesStrip, getFavoriteChannels().slice(0, 8), "No favorites saved yet.");
  renderSavedStrip(elements.recentStrip, getRecentChannels().slice(0, 8), "Recent plays will appear here.");
}

function getBaseCollection() {
  if (state.activeView === "favorites") {
    return getFavoriteChannels();
  }
  if (state.activeView === "recent") {
    return getRecentChannels();
  }
  return state.items;
}

function getFilteredChannels() {
  const search = elements.searchInput.value.trim().toLowerCase();
  const category = state.activeCategory;
  const country = elements.countrySelect.value;

  return getBaseCollection().filter((channel) => {
    const matchesSearch =
      !search ||
      channel.name.toLowerCase().includes(search) ||
      channel.country.toLowerCase().includes(search) ||
      channel.category.toLowerCase().includes(search) ||
      channel.url.toLowerCase().includes(search);
    const matchesCategory = category === "All" || channel.category === category;
    const matchesCountry = country === "All" || channel.country === country;
    return matchesSearch && matchesCategory && matchesCountry;
  });
}

function syncFavoriteButton() {
  const saved = state.selectedChannel && isFavorite(state.selectedChannel);
  elements.favoriteButton.textContent = saved ? "Saved Favorite" : "Save Favorite";
}

function renderChannels(channels, totalCount, startIndex) {
  elements.channelGrid.innerHTML = "";
  elements.emptyState.classList.toggle("hidden", channels.length > 0);

  channels.forEach((channel) => {
    const card = document.createElement("article");
    card.className = "channel-card";
    if (state.selectedChannel?.url === channel.url) {
      card.classList.add("active");
    }

    const titleRow = document.createElement("div");
    titleRow.className = "card-title-row";

    const title = document.createElement("h3");
    title.textContent = channel.name;

    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.className = "save-chip";
    saveButton.textContent = isFavorite(channel) ? "Saved" : "Save";
    saveButton.addEventListener("click", () => toggleFavorite(channel));

    titleRow.append(title, saveButton);

    const tags = document.createElement("div");
    tags.className = "channel-tags";
    [channel.country, channel.category].filter(Boolean).forEach((value) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = value;
      tags.appendChild(tag);
    });

    const url = document.createElement("p");
    url.className = "channel-url";
    url.textContent = channel.url;

    const actions = document.createElement("div");
    actions.className = "channel-actions";

    const playButton = document.createElement("button");
    playButton.className = "accent-button";
    playButton.type = "button";
    playButton.textContent = "Play Here";
    playButton.addEventListener("click", () => activatePlayer(channel));

    const openLink = document.createElement("a");
    openLink.className = "ghost-button";
    openLink.href = channel.url;
    openLink.target = "_blank";
    openLink.rel = "noreferrer";
    openLink.textContent = "Open Stream";

    actions.append(playButton, openLink);
    card.append(titleRow, tags, url, actions);
    elements.channelGrid.appendChild(card);
  });

  if (totalCount === 0) {
    elements.resultsCaption.textContent = "No channels matched the current filters.";
  } else {
    const rangeStart = startIndex + 1;
    const rangeEnd = startIndex + channels.length;
    elements.resultsCaption.textContent =
      totalCount === channels.length
        ? `${totalCount.toLocaleString()} channel${totalCount === 1 ? "" : "s"} matched the current filters.`
        : `Showing ${rangeStart.toLocaleString()}–${rangeEnd.toLocaleString()} of ${totalCount.toLocaleString()} channels.`;
  }
}

function renderRefreshStatus() {
  const refreshState = state.refreshState;
  if (!refreshState) {
    elements.refreshStatusText.textContent = "Ready to sync the latest channels.";
    return;
  }

  const tokenLabel = refreshState.admin_token_required ? " Admin token required." : "";
  elements.refreshStatusText.textContent = `${refreshState.message}${tokenLabel}`;
  const busy = refreshState.status === "running";
  elements.syncButton.disabled = busy;
  elements.syncButton.textContent = busy ? "Syncing..." : "Sync Catalog";
}

function updatePagination(totalCount, totalPages) {
  elements.paginationIndicator.textContent = totalCount === 0 ? "No results" : `Page ${state.page} of ${totalPages}`;
  elements.paginationPrev.disabled = state.page <= 1;
  elements.paginationNext.disabled = state.page >= totalPages;
}

function renderFromState() {
  const filtered = getFilteredChannels();
  const totalPages = Math.max(1, Math.ceil(filtered.length / CHANNELS_PER_PAGE));
  state.page = Math.min(Math.max(1, state.page), totalPages);
  const startIndex = (state.page - 1) * CHANNELS_PER_PAGE;
  const pageItems = filtered.slice(startIndex, startIndex + CHANNELS_PER_PAGE);

  renderStats(filtered.length);
  renderSavedCollections();
  renderChannels(pageItems, filtered.length, startIndex);
  syncFavoriteButton();
  renderRefreshStatus();
  updatePagination(filtered.length, totalPages);
}

function cleanupPlayer() {
  if (state.hls) {
    state.hls.destroy();
    state.hls = null;
  }
  elements.player.pause();
  elements.player.removeAttribute("src");
  elements.player.load();
}

function showPlayerLoading() {
  elements.playerLoading.classList.remove("hidden");
}

function hidePlayerLoading() {
  elements.playerLoading.classList.add("hidden");
}

async function ensureHlsLibrary() {
  if (window.Hls) {
    return window.Hls;
  }

  if (state.hlsLoadAttempted) {
    return null;
  }

  state.hlsLoadAttempted = true;

  return new Promise((resolve) => {
    const existing = document.querySelector(`script[src="${HLS_SCRIPT_URL}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve(window.Hls || null), { once: true });
      existing.addEventListener("error", () => resolve(null), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = HLS_SCRIPT_URL;
    script.async = true;
    script.addEventListener("load", () => resolve(window.Hls || null), { once: true });
    script.addEventListener("error", () => resolve(null), { once: true });
    document.head.appendChild(script);
  });
}

function attemptPlayback() {
  elements.player.play().catch(() => {
    // Autoplay may be blocked; native controls still allow playback.
  });
}

async function activatePlayer(channel) {
  state.selectedChannel = channel;
  rememberChannel(channel);
  syncFavoriteButton();

  elements.currentChannelName.textContent = channel.name;
  elements.currentChannelMeta.textContent = `${formatMeta(channel)} | ${channel.url}`;
  elements.playerPlaceholder.classList.add("hidden");
  elements.openStreamLink.href = channel.url;
  elements.openStreamLink.classList.remove("disabled-link");

  cleanupPlayer();
  showPlayerLoading();

  const isHls = /\.m3u8($|[?#])/i.test(channel.url);
  const isDash = /\.mpd($|[?#])/i.test(channel.url);
  const nativeHls = Boolean(elements.player.canPlayType("application/vnd.apple.mpegurl"));
  const nativeDash = Boolean(elements.player.canPlayType("application/dash+xml"));

  if (isHls && !nativeHls) {
    const HlsCtor = await ensureHlsLibrary();
    if (HlsCtor?.isSupported?.()) {
      const hls = new HlsCtor({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
      });
      let recoveryAttempted = false;
      state.hls = hls;
      hls.attachMedia(elements.player);
      hls.on(HlsCtor.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(channel.url);
      });
      hls.on(HlsCtor.Events.MANIFEST_PARSED, () => {
        setPlayerMode("Expanded browser playback via HLS.js.", true);
        attemptPlayback();
      });
      hls.on(HlsCtor.Events.ERROR, (_, data) => {
        if (!data?.fatal) {
          return;
        }
        // Public IPTV streams can hiccup transiently - give recovery one try
        // before giving up and pointing the viewer at "Open Stream".
        if (!recoveryAttempted) {
          recoveryAttempted = true;
          if (data.type === HlsCtor.ErrorTypes.NETWORK_ERROR) {
            setPlayerMode("Connection hiccup - retrying...", true);
            hls.startLoad();
            return;
          }
          if (data.type === HlsCtor.ErrorTypes.MEDIA_ERROR) {
            setPlayerMode("Playback hiccup - recovering...", true);
            hls.recoverMediaError();
            return;
          }
        }
        hidePlayerLoading();
        setPlayerMode("Browser playback failed. Use Open Stream for this channel.", false);
      });
      renderFromState();
      return;
    }
  }

  elements.player.src = channel.url;
  elements.player.load();

  if ((isHls && nativeHls) || (isDash && nativeDash)) {
    setPlayerMode("Native browser streaming is available for this channel.", true);
  } else if (isHls || isDash) {
    setPlayerMode("Browser support for this stream is limited. Try Open Stream if needed.", false);
  } else {
    setPlayerMode("Attempting direct browser playback for this stream.", true);
  }

  attemptPlayback();
  renderFromState();
}

function stepChannel(delta) {
  const filtered = getFilteredChannels();
  if (!filtered.length) {
    return;
  }

  const currentIndex = state.selectedChannel
    ? filtered.findIndex((channel) => channel.url === state.selectedChannel.url)
    : -1;
  const nextIndex = (((currentIndex === -1 ? 0 : currentIndex + delta) % filtered.length) + filtered.length) % filtered.length;
  const nextChannel = filtered[nextIndex];
  state.page = Math.floor(nextIndex / CHANNELS_PER_PAGE) + 1;
  activatePlayer(nextChannel);
}

function toggleFavorite(channel = state.selectedChannel) {
  if (!channel?.url) {
    return;
  }

  if (state.favorites.has(channel.url)) {
    state.favorites.delete(channel.url);
  } else {
    state.favorites.add(channel.url);
  }

  persistFavorites();
  renderFromState();
}

const CHANNELS_PAGE_SIZE = 2000;

async function fetchAllChannels(onProgress) {
  const items = [];
  let offset = 0;

  while (true) {
    const page = await fetchJson(`/channels?limit=${CHANNELS_PAGE_SIZE}&offset=${offset}`);
    const pageItems = page.items || [];
    items.push(...pageItems);
    offset += pageItems.length;
    onProgress?.(items.length, page.total ?? items.length);
    if (pageItems.length === 0 || offset >= (page.total ?? offset)) {
      break;
    }
  }

  return items;
}

async function refreshData({ keepSelection = true } = {}) {
  setApiStatus("Connecting...", true);
  elements.resultsCaption.textContent = "Loading channels...";

  try {
    const [health, channels, categories, countries, source, refreshState] = await Promise.all([
      fetchJson("/health"),
      fetchAllChannels((loaded, total) => {
        elements.resultsCaption.textContent = `Loading channels... ${loaded.toLocaleString()} of ${total.toLocaleString()}`;
      }),
      fetchJson("/channels/categories"),
      fetchJson("/channels/countries"),
      fetchJson("/channels/source"),
      fetchJson("/admin/refresh"),
    ]);

    const previousSelection = keepSelection ? state.selectedChannel?.url : null;
    state.items = channels || [];
    state.categories = categories.items || [];
    state.countries = countries.items || [];
    state.refreshState = refreshState;
    state.history = sanitizeRecentItems(state.history);

    if (!state.categories.includes(state.activeCategory)) {
      state.activeCategory = "All";
    }
    renderCategoryChips();
    populateSelect(elements.countrySelect, state.countries);
    elements.sourceMeta.textContent = `${source.channel_count} channels from ${source.channels_file}`;
    setApiStatus(`API ${health.version}`, true);

    const nextSelection = previousSelection ? findChannelByUrl(previousSelection) : null;
    if (nextSelection) {
      state.selectedChannel = nextSelection;
    } else if (!state.selectedChannel && state.items.length > 0) {
      state.selectedChannel = state.items[0];
    }

    renderFromState();
  } catch (error) {
    console.error(error);
    setApiStatus("API unavailable", false);
    elements.resultsCaption.textContent = "Could not load channels from the local API.";
    elements.sourceMeta.textContent = "Start the backend with tv_main.py --serve-api";
    elements.channelGrid.innerHTML = "";
    elements.emptyState.classList.remove("hidden");
    setPlayerMode("Backend unavailable. Start the local API to continue.", false);
  }
}

async function startCatalogSync() {
  persistAdminToken();
  elements.syncButton.disabled = true;
  elements.syncButton.textContent = "Syncing...";
  elements.refreshStatusText.textContent = "Refreshing the shared catalog. This can take a little while.";

  const params = new URLSearchParams({
    limit: "0",
  });
  if (elements.verifyLiveCheckbox.checked) {
    params.set("verify_live", "true");
  }

  try {
    state.refreshState = await fetchJson(`/admin/refresh?${params.toString()}`, {
      method: "POST",
    });
    await refreshData({ keepSelection: false });
  } catch (error) {
    console.error(error);
    const detail = error.payload?.detail || "Refresh failed. Check the admin token or source availability.";
    elements.refreshStatusText.textContent = detail;
    elements.syncButton.disabled = false;
    elements.syncButton.textContent = "Sync Catalog";
  }
}

const debouncedRenderFromState = debounce(renderFromState, 150);

elements.searchInput.addEventListener("input", () => {
  state.page = 1;
  debouncedRenderFromState();
});
elements.countrySelect.addEventListener("change", () => {
  state.page = 1;
  renderFromState();
});
elements.viewTabs.querySelectorAll(".segmented-button").forEach((button) => {
  button.addEventListener("click", () => setActiveView(button.dataset.view));
});
elements.reloadButton.addEventListener("click", () => refreshData());
elements.syncButton.addEventListener("click", startCatalogSync);
elements.favoriteButton.addEventListener("click", () => toggleFavorite());
elements.favoritesOnlyButton.addEventListener("click", () => setActiveView("favorites"));
elements.recentOnlyButton.addEventListener("click", () => setActiveView("recent"));
elements.resetFilters.addEventListener("click", () => {
  elements.searchInput.value = "";
  elements.countrySelect.value = "All";
  state.activeCategory = "All";
  state.activeView = "all";
  state.page = 1;
  renderCategoryChips();
  updateViewTabs();
  renderFromState();
});
elements.adminTokenInput.addEventListener("change", persistAdminToken);

elements.settingsButton.addEventListener("click", () => {
  const collapsed = elements.adminPanel.classList.toggle("collapsed");
  elements.settingsButton.setAttribute("aria-expanded", String(!collapsed));
});

elements.paginationPrev.addEventListener("click", () => {
  state.page -= 1;
  renderFromState();
  elements.channelGrid.scrollIntoView({ behavior: "smooth", block: "start" });
});
elements.paginationNext.addEventListener("click", () => {
  state.page += 1;
  renderFromState();
  elements.channelGrid.scrollIntoView({ behavior: "smooth", block: "start" });
});

elements.copyStreamButton.addEventListener("click", async () => {
  if (!state.selectedChannel?.url) {
    return;
  }

  try {
    await navigator.clipboard.writeText(state.selectedChannel.url);
    elements.copyStreamButton.textContent = "Copied";
    window.setTimeout(() => {
      elements.copyStreamButton.textContent = "Copy URL";
    }, 1400);
  } catch (error) {
    console.error(error);
    elements.copyStreamButton.textContent = "Copy Failed";
    window.setTimeout(() => {
      elements.copyStreamButton.textContent = "Copy URL";
    }, 1600);
  }
});

elements.player.addEventListener("error", () => {
  hidePlayerLoading();
  setPlayerMode("This browser could not play the stream directly. Try Open Stream.", false);
});
elements.player.addEventListener("waiting", showPlayerLoading);
elements.player.addEventListener("playing", hidePlayerLoading);
elements.player.addEventListener("canplay", hidePlayerLoading);

elements.fullscreenButton.addEventListener("click", () => {
  if (!document.fullscreenElement) {
    elements.playerFrame.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
});
document.addEventListener("fullscreenchange", () => {
  const isFullscreen = document.fullscreenElement === elements.playerFrame;
  elements.fullscreenButton.textContent = isFullscreen ? "⤢" : "⛶";
  elements.fullscreenButton.title = isFullscreen ? "Exit fullscreen" : "Fullscreen";
});

if (document.pictureInPictureEnabled) {
  elements.pipButton.hidden = false;
  elements.pipButton.addEventListener("click", async () => {
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      } else if (elements.player.readyState > 0) {
        await elements.player.requestPictureInPicture();
      }
    } catch (error) {
      console.error(error);
    }
  });
}

document.addEventListener("keydown", (event) => {
  const target = event.target;
  const isTyping = target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
  if (isTyping) {
    return;
  }

  if (event.code === "Space") {
    event.preventDefault();
    if (elements.player.paused) {
      attemptPlayback();
    } else {
      elements.player.pause();
    }
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    stepChannel(1);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    stepChannel(-1);
  } else if (event.key.toLowerCase() === "f") {
    elements.fullscreenButton.click();
  } else if (event.key.toLowerCase() === "m") {
    elements.player.muted = !elements.player.muted;
  }
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  state.deferredInstallPrompt = event;
  elements.installButton.hidden = false;
});

elements.installButton.addEventListener("click", async () => {
  const prompt = state.deferredInstallPrompt;
  if (!prompt) {
    return;
  }
  elements.installButton.hidden = true;
  state.deferredInstallPrompt = null;
  await prompt.prompt();
});

window.addEventListener("appinstalled", () => {
  elements.installButton.hidden = true;
  state.deferredInstallPrompt = null;
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch((error) => {
      console.error("Service worker registration failed", error);
    });
  });
}

loadStoredState();
updateViewTabs();
refreshData().then(() => {
  if (state.selectedChannel) {
    activatePlayer(state.selectedChannel);
  }
});
