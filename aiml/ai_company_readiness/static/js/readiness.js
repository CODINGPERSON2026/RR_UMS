/**
 * AI Company Readiness JavaScript Library
 * Handles AJAX drill-down, personnel filtering, snapshot recording, and interactive modal displays.
 */

document.addEventListener("DOMContentLoaded", function () {
  initPersonnelSearch();
});

/**
 * Captures current readiness snapshot for historical record logging.
 */
function recordReadinessSnapshot(btnElement) {
  if (!btnElement) return;
  const originalHtml = btnElement.innerHTML;
  btnElement.disabled = true;
  btnElement.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Saving Snapshot...`;

  fetch("/ai-company-readiness/api/snapshot", {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  })
    .then((res) => res.json())
    .then((data) => {
      btnElement.disabled = false;
      btnElement.innerHTML = originalHtml;
      if (data.success) {
        showReadinessToast("Snapshot Recorded", data.message, "success");
      } else {
        showReadinessToast("Error", data.error || "Failed to record snapshot", "danger");
      }
    })
    .catch((err) => {
      btnElement.disabled = false;
      btnElement.innerHTML = originalHtml;
      showReadinessToast("Network Error", "Could not reach UMS server", "danger");
    });
}

/**
 * Opens Personnel Drill-Down Modal and loads records asynchronously.
 */
function openPersonnelDrilldownModal(company, gapType, gapName) {
  const modalEl = document.getElementById("personnelDrilldownModal");
  if (!modalEl) {
    // If modal not on page, navigate directly to gap details page
    window.location.href = `/ai-company-readiness/company/${encodeURIComponent(company)}/gaps?type=${encodeURIComponent(gapType)}&name=${encodeURIComponent(gapName || gapType)}`;
    return;
  }

  const modalTitle = document.getElementById("drilldownModalTitle");
  const modalSubtitle = document.getElementById("drilldownModalSubtitle");
  const tableBody = document.getElementById("drilldownTableBody");
  const modalLoading = document.getElementById("drilldownLoading");

  if (modalTitle) modalTitle.innerText = `${gapType} Gap Drill-Down: ${gapName || gapType}`;
  if (modalSubtitle) modalSubtitle.innerText = `Formation: ${company} • Identified Contributing Personnel`;
  if (tableBody) tableBody.innerHTML = "";
  if (modalLoading) modalLoading.style.display = "block";

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  const url = `/ai-company-readiness/company/${encodeURIComponent(company)}/personnel?type=${encodeURIComponent(gapType)}&name=${encodeURIComponent(gapName || gapType)}`;
  fetch(url)
    .then((res) => res.json())
    .then((data) => {
      if (modalLoading) modalLoading.style.display = "none";
      if (!data.success || !data.personnel || data.personnel.length === 0) {
        if (tableBody) {
          tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No contributing personnel records found for this gap.</td></tr>`;
        }
        return;
      }

      let html = "";
      data.personnel.forEach((p, idx) => {
        html += `
          <tr>
            <td class="fw-bold">${idx + 1}</td>
            <td><span class="badge bg-secondary font-monospace">${p.army_number || "-"}</span></td>
            <td class="fw-semibold">${p.name || "Unknown"}</td>
            <td>${p.rank || "-"}</td>
            <td>${p.trade || "-"}</td>
            <td><span class="text-danger fw-bold">${p.reason || p.gap_category || "-"}</span></td>
            <td><span class="text-success fw-semibold"><i class="fas fa-check-circle me-1" style="font-size: 0.78rem;"></i>${p.solution || "Review & resolve"}</span></td>
          </tr>
        `;
      });
      if (tableBody) tableBody.innerHTML = html;
    })
    .catch((err) => {
      if (modalLoading) modalLoading.style.display = "none";
      if (tableBody) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Failed to load drill-down data: ${err.message}</td></tr>`;
      }
    });
}

/**
 * Filter drilldown table records by search input
 */
function initPersonnelSearch() {
  const searchInput = document.getElementById("drilldownSearchInput");
  if (!searchInput) return;

  searchInput.addEventListener("input", function () {
    const filter = this.value.toLowerCase();
    const rows = document.querySelectorAll("#drilldownTableBody tr");

    rows.forEach((row) => {
      const text = row.innerText.toLowerCase();
      row.style.display = text.includes(filter) ? "" : "none";
    });
  });
}

/**
 * Displays a lightweight toast notification
 */
function showReadinessToast(title, message, type) {
  const toastContainer = document.getElementById("readinessToastContainer");
  if (!toastContainer) {
    alert(`${title}: ${message}`);
    return;
  }

  const toastId = "toast_" + Date.now();
  const bgClass = type === "success" ? "bg-success" : "bg-danger";

  const toastHtml = `
    <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">
          <strong>${title}:</strong> ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;

  toastContainer.insertAdjacentHTML("beforeend", toastHtml);
  const toastEl = document.getElementById(toastId);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
  bsToast.show();

  toastEl.addEventListener("hidden.bs.toast", () => {
    toastEl.remove();
  });
}

/**
 * 5-Second Countdown Timer for Under Development Banner
 */
let devBannerTimerInterval = null;
const DEV_BANNER_MS = 5000;

function startDevNoticeTimer() {
  const banner = document.getElementById("devNoticeBanner");
  const countdownEl = document.getElementById("bannerTimerCountdown");
  const fillEl = document.getElementById("bannerProgressFill");
  if (!banner) return;

  const startTime = Date.now();
  if (devBannerTimerInterval) clearInterval(devBannerTimerInterval);

  devBannerTimerInterval = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const remainingRatio = Math.max(0, 1 - (elapsed / DEV_BANNER_MS));

    if (fillEl) {
      fillEl.style.width = (remainingRatio * 100) + "%";
    }

    const secsLeft = Math.max(0, Math.ceil((DEV_BANNER_MS - elapsed) / 1000));
    if (countdownEl && countdownEl.textContent !== String(secsLeft)) {
      countdownEl.textContent = secsLeft;
    }

    if (elapsed >= DEV_BANNER_MS) {
      clearInterval(devBannerTimerInterval);
      devBannerTimerInterval = null;
      dismissDevNoticeBanner();
    }
  }, 50);
}

function dismissDevNoticeBanner() {
  const banner = document.getElementById("devNoticeBanner");
  if (!banner) return;

  if (devBannerTimerInterval) {
    clearInterval(devBannerTimerInterval);
    devBannerTimerInterval = null;
  }

  banner.classList.add("banner-closing");
  setTimeout(() => {
    banner.classList.add("banner-hidden");
    banner.style.display = "none";
  }, 480);
}

/**
 * Multi-criteria Dropdown Filter for Readiness Dashboard Formations
 */
function applyDropdownFilters() {
  const companySelect = document.getElementById("filterCompanyDropdown");
  const statusSelect = document.getElementById("filterStatusDropdown");
  const gapSelect = document.getElementById("filterGapDropdown");
  const sortSelect = document.getElementById("filterSortDropdown");

  const selectedCompany = companySelect ? companySelect.value : "all";
  const selectedStatus = statusSelect ? statusSelect.value : "all";
  const selectedGap = gapSelect ? gapSelect.value : "all";
  const selectedSort = sortSelect ? sortSelect.value : "default";

  // Sync quick select pills
  document.querySelectorAll(".filter-coy-btn").forEach((btn) => {
    const pillCoy = btn.getAttribute("data-coy");
    if (pillCoy === selectedCompany) {
      btn.classList.remove("btn-outline-secondary");
      btn.classList.add("btn-primary", "active");
    } else {
      btn.classList.remove("btn-primary", "active");
      btn.classList.add("btn-outline-secondary");
    }
  });

  const cardsContainer = document.getElementById("companyCardsGrid");
  const cards = Array.from(document.querySelectorAll(".coy-card"));
  let visibleCount = 0;

  cards.forEach((card) => {
    const coy = card.getAttribute("data-company") || "";
    const status = card.getAttribute("data-status") || "";
    const gap = card.getAttribute("data-gap") || "";

    const matchCompany = (selectedCompany === "all" || coy === selectedCompany);
    const matchStatus = (selectedStatus === "all" || status.toLowerCase() === selectedStatus.toLowerCase());
    const matchGap = (selectedGap === "all" || gap.toLowerCase() === selectedGap.toLowerCase());

    if (matchCompany && matchStatus && matchGap) {
      card.style.display = "flex";
      visibleCount++;
    } else {
      card.style.display = "none";
    }
  });

  // Sorting
  if (cardsContainer) {
    if (selectedSort === "score-desc") {
      cards.sort((a, b) => parseFloat(b.getAttribute("data-readiness") || 0) - parseFloat(a.getAttribute("data-readiness") || 0));
      cards.forEach((c) => cardsContainer.appendChild(c));
    } else if (selectedSort === "score-asc") {
      cards.sort((a, b) => parseFloat(a.getAttribute("data-readiness") || 0) - parseFloat(b.getAttribute("data-readiness") || 0));
      cards.forEach((c) => cardsContainer.appendChild(c));
    } else if (selectedSort === "strength-desc") {
      cards.sort((a, b) => parseInt(b.getAttribute("data-strength") || 0) - parseInt(a.getAttribute("data-strength") || 0));
      cards.forEach((c) => cardsContainer.appendChild(c));
    } else {
      cards.sort((a, b) => parseInt(a.getAttribute("data-order") || 0) - parseInt(b.getAttribute("data-order") || 0));
      cards.forEach((c) => cardsContainer.appendChild(c));
    }
  }

  // Update badge counter
  const badge = document.getElementById("filteredCountBadge");
  if (badge) {
    badge.textContent = `Showing ${visibleCount} of ${cards.length} Formations`;
    if (visibleCount === 0) {
      badge.className = "badge rounded-pill bg-danger ms-1";
    } else if (visibleCount < cards.length) {
      badge.className = "badge rounded-pill bg-warning text-dark ms-1";
    } else {
      badge.className = "badge rounded-pill bg-primary ms-1";
    }
  }

  // Show/Hide empty state
  const noMatchAlert = document.getElementById("noMatchAlert");
  if (noMatchAlert) {
    noMatchAlert.style.display = (visibleCount === 0) ? "block" : "none";
  }
}

function selectCompanyPill(coyName) {
  const companySelect = document.getElementById("filterCompanyDropdown");
  if (companySelect) {
    companySelect.value = coyName;
    applyDropdownFilters();
  }
}

function filterCompanyCards(coyName, btnEl) {
  selectCompanyPill(coyName);
}

function resetAllFilters() {
  const companySelect = document.getElementById("filterCompanyDropdown");
  const statusSelect = document.getElementById("filterStatusDropdown");
  const gapSelect = document.getElementById("filterGapDropdown");
  const sortSelect = document.getElementById("filterSortDropdown");

  if (companySelect) companySelect.value = "all";
  if (statusSelect) statusSelect.value = "all";
  if (gapSelect) gapSelect.value = "all";
  if (sortSelect) sortSelect.value = "default";

  applyDropdownFilters();
}

