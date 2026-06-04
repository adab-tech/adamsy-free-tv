const STORAGE_KEYS = {
  favorites: "adamsy-free-tv:favorites",
  history: "adamsy-free-tv:history",
  adminToken: "adamsy-free-tv:admin-token",
};

const HLS_SCRIPT_URL = "https://cdn.jsdelivr.net/npm/hls.js@1";

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
  categorySelect: document.querySelector("#category-select"),
  countrySelect: document.querySelector("#country-select"),
  viewSelect: document.querySelector("#view-select"),
  searchInput: document.querySelector("#search-input"),
  reloadButton: document.querySelector("#reload-button"),
  syncButton: document.querySelector("#sync-button"),
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
  player: document.querySelector("#channel-player"),
  playerPlaceholder: document.querySelector("#player-placeholder"),
  playerMode: document.querySelector("#player-mode"),
  currentChannelName: document.querySelector("#current-channel-name"),
  currentChannelMeta: document.querySelector("#current-channel-meta"),
  favoriteButton: document.querySelector("#favorite-button"),
  openStreamLink: document.querySelector("#open-stream-link"),
  copyStreamButton: document.querySelector("#copy-stream-button"),
};

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
  const view = elements.viewSelect.value;
  if (view === "favorites") {
    return getFavoriteChannels();
  }
  if (view === "recent") {
    return getRecentChannels();
  }
  return state.items;
}

function getFilteredChannels() {
  const search = elements.searchInput.value.trim().toLowerCase();
  const category = elements.categorySelect.value;
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

function renderChannels(channels) {
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

  elements.resultsCaption.textContent =
    channels.length === 1
      ? "1 channel matched the current filters."
      : `${channels.length} channels matched the current filters.`;
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

function renderFromState() {
  const filtered = getFilteredChannels();
  renderStats(filtered.length);
  renderSavedCollections();
  renderChannels(filtered);
  syncFavoriteButton();
  renderRefreshStatus();
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
      });
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
        if (data?.fatal) {
          setPlayerMode("Browser playback failed. Use Open Stream for this channel.", false);
        }
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

async function refreshData({ keepSelection = true } = {}) {
  setApiStatus("Connecting...", true);

  try {
    const [health, channels, categories, countries, source, refreshState] = await Promise.all([
      fetchJson("/health"),
      fetchJson("/channels?limit=1000"),
      fetchJson("/channels/categories"),
      fetchJson("/channels/countries"),
      fetchJson("/channels/source"),
      fetchJson("/admin/refresh"),
    ]);

    const previousSelection = keepSelection ? state.selectedChannel?.url : null;
    state.items = channels.items || [];
    state.categories = categories.items || [];
    state.countries = countries.items || [];
    state.refreshState = refreshState;
    state.history = sanitizeRecentItems(state.history);

    populateSelect(elements.categorySelect, state.categories);
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
    limit: "700",
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

elements.searchInput.addEventListener("input", renderFromState);
elements.categorySelect.addEventListener("change", renderFromState);
elements.countrySelect.addEventListener("change", renderFromState);
elements.viewSelect.addEventListener("change", renderFromState);
elements.reloadButton.addEventListener("click", () => refreshData());
elements.syncButton.addEventListener("click", startCatalogSync);
elements.favoriteButton.addEventListener("click", () => toggleFavorite());
elements.favoritesOnlyButton.addEventListener("click", () => {
  elements.viewSelect.value = "favorites";
  renderFromState();
});
elements.recentOnlyButton.addEventListener("click", () => {
  elements.viewSelect.value = "recent";
  renderFromState();
});
elements.resetFilters.addEventListener("click", () => {
  elements.searchInput.value = "";
  elements.categorySelect.value = "All";
  elements.countrySelect.value = "All";
  elements.viewSelect.value = "all";
  renderFromState();
});
elements.adminTokenInput.addEventListener("change", persistAdminToken);

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
  setPlayerMode("This browser could not play the stream directly. Try Open Stream.", false);
});

loadStoredState();
refreshData().then(() => {
  if (state.selectedChannel) {
    activatePlayer(state.selectedChannel);
  }
});
