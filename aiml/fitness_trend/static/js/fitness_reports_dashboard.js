/**
 * AI Fitness Reports Executive Dashboard Controller
 * Handles live stats, search, filtering, server-side pagination, sorting,
 * multi-tab modal report views, PDF export, and report regeneration.
 */

(function () {
  'use strict';

  // State
  const state = {
    search: '',
    company: '',
    status: '',
    fromDate: '',
    toDate: '',
    sortBy: 'generated_at',
    sortOrder: 'desc',
    page: 1,
    perPage: 10,
    totalRecords: 0,
    totalPages: 1,
    currentReportData: null
  };

  let searchTimeout = null;

  // DOM Elements
  const el = {
    statTotal: document.getElementById('statTotalReports'),
    statHealthy: document.getElementById('statHealthyReports'),
    statNeedsImp: document.getElementById('statNeedsImpReports'),
    statAtRisk: document.getElementById('statAtRiskReports'),
    
    searchInput: document.getElementById('filterSearchInput'),
    companySelect: document.getElementById('filterCompanySelect'),
    statusSelect: document.getElementById('filterStatusSelect'),
    fromDateInput: document.getElementById('filterFromDate'),
    toDateInput: document.getElementById('filterToDate'),
    resetBtn: document.getElementById('btnResetFilters'),
    
    tableBody: document.getElementById('reportsTableBody'),
    resultsInfo: document.getElementById('resultsCounterText'),
    paginationNav: document.getElementById('paginationControls'),
    pageSizeSelect: document.getElementById('pageSizeSelect'),
    
    // Modal
    reportModal: null, // Bootstrap modal instance
    modalSoldierTitle: document.getElementById('modalSoldierTitle'),
    modalSoldierMeta: document.getElementById('modalSoldierMeta'),
    modalPdfBtn: document.getElementById('modalDownloadPdfBtn'),
    tabContentOverview: document.getElementById('tabPaneOverview'),
    tabContentAnalysis: document.getElementById('tabPaneAnalysis'),
    tabContentRecs: document.getElementById('tabPaneRecs'),
    tabContentProgression: document.getElementById('tabPaneProgression')
  };

  function ensureReportModalInstance() {
    if (el.reportModal) return el.reportModal;
    const modalElement = document.getElementById('reportDetailModal');
    if (!modalElement) return null;
    if (window.bootstrap && window.bootstrap.Modal) {
      el.reportModal = new bootstrap.Modal(modalElement);
    } else if (window.$ && typeof $(modalElement).modal === 'function') {
      el.reportModal = {
        show: function() { $(modalElement).modal('show'); },
        hide: function() { $(modalElement).modal('hide'); }
      };
    }
    return el.reportModal;
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', () => {
    ensureReportModalInstance();
    attachEventListeners();
    loadDashboardStats();
    loadReportsData();
  });

  function attachEventListeners() {
    // Search with debounce
    if (el.searchInput) {
      el.searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          state.search = e.target.value.trim();
          state.page = 1;
          loadReportsData();
        }, 350);
      });
    }

    // Company filter
    if (el.companySelect) {
      el.companySelect.addEventListener('change', (e) => {
        state.company = e.target.value;
        state.page = 1;
        loadReportsData();
      });
    }

    // Status filter
    if (el.statusSelect) {
      el.statusSelect.addEventListener('change', (e) => {
        state.status = e.target.value;
        state.page = 1;
        updateActiveMetricCard(state.status);
        loadReportsData();
      });
    }

    // Date range
    if (el.fromDateInput) {
      el.fromDateInput.addEventListener('change', (e) => {
        state.fromDate = e.target.value;
        state.page = 1;
        loadReportsData();
      });
    }
    if (el.toDateInput) {
      el.toDateInput.addEventListener('change', (e) => {
        state.toDate = e.target.value;
        state.page = 1;
        loadReportsData();
      });
    }

    // Page size
    if (el.pageSizeSelect) {
      el.pageSizeSelect.addEventListener('change', (e) => {
        state.perPage = parseInt(e.target.value, 10) || 10;
        state.page = 1;
        loadReportsData();
      });
    }

    // Reset filters
    if (el.resetBtn) {
      el.resetBtn.addEventListener('click', () => {
        state.search = '';
        state.company = '';
        state.status = '';
        state.fromDate = '';
        state.toDate = '';
        state.page = 1;
        
        if (el.searchInput) el.searchInput.value = '';
        if (el.companySelect) el.companySelect.value = '';
        if (el.statusSelect) el.statusSelect.value = '';
        if (el.fromDateInput) el.fromDateInput.value = '';
        if (el.toDateInput) el.toDateInput.value = '';
        
        updateActiveMetricCard('');
        loadReportsData();
      });
    }

    // Sorting headers
    document.querySelectorAll('.reports-table th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const field = th.getAttribute('data-sort');
        if (!field) return;

        if (state.sortBy === field) {
          state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
          state.sortBy = field;
          state.sortOrder = 'desc';
        }
        
        // Update header UI indicator
        document.querySelectorAll('.reports-table th.sortable i').forEach(icon => {
          icon.className = 'fas fa-sort text-muted ms-1';
        });
        const currentIcon = th.querySelector('i');
        if (currentIcon) {
          currentIcon.className = state.sortOrder === 'asc' ? 'fas fa-sort-up text-primary ms-1' : 'fas fa-sort-down text-primary ms-1';
        }

        loadReportsData();
      });
    });

    // Modal Tabs Navigation
    document.querySelectorAll('#reportModalTabs button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('#reportModalTabs button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane-custom').forEach(p => p.classList.remove('active'));
        
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-target');
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add('active');
      });
    });
  }

  function filterByStatus(status) {
    state.status = status || '';
    state.page = 1;
    if (el.statusSelect) {
      el.statusSelect.value = state.status;
    }
    updateActiveMetricCard(state.status);
    loadReportsData();
  }

  function updateActiveMetricCard(status) {
    document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active-filter'));
    const sLower = (status || '').toLowerCase();
    if (!sLower) {
      document.getElementById('dashMetricTotal')?.classList.add('active-filter');
    } else if (sLower.includes('healthy') || sLower.includes('ready')) {
      document.getElementById('dashMetricHealthy')?.classList.add('active-filter');
    } else if (sLower.includes('improve')) {
      document.getElementById('dashMetricNeedsImp')?.classList.add('active-filter');
    } else if (sLower.includes('risk') || sLower.includes('attention')) {
      document.getElementById('dashMetricAtRisk')?.classList.add('active-filter');
    }
  }

  /**
   * Fetches real-time aggregate statistics for executive cards
   */
  async function loadDashboardStats() {
    try {
      const resp = await fetch('/fitness/api/reports/stats');
      if (!resp.ok) {
        console.warn('Could not fetch reports stats:', resp.status);
        return;
      }
      const data = await resp.json();
      if (data.success && data.stats) {
        const s = data.stats;
        if (el.statTotal) el.statTotal.textContent = s.total_reports || 0;
        if (el.statHealthy) el.statHealthy.textContent = s.healthy_count || 0;
        if (el.statNeedsImp) el.statNeedsImp.textContent = s.needs_improvement_count || 0;
        if (el.statAtRisk) el.statAtRisk.textContent = s.at_risk_count || 0;
      }
    } catch (err) {
      console.error('Error loading report stats:', err);
    }
  }

  /**
   * Fetches paginated reports table data from server
   */
  async function loadReportsData() {
    renderLoadingTable();

    const params = new URLSearchParams({
      search: state.search,
      company: state.company,
      status: state.status,
      from_date: state.fromDate,
      to_date: state.toDate,
      sort_by: state.sortBy,
      sort_order: state.sortOrder,
      page: state.page,
      per_page: state.perPage
    });

    try {
      const resp = await fetch(`/fitness/api/reports?${params.toString()}`);
      if (resp.status === 403) {
        renderForbiddenState();
        return;
      }
      if (!resp.ok) {
        throw new Error(`Server returned HTTP ${resp.status}`);
      }

      const res = await resp.json();
      if (!res.success) {
        throw new Error(res.error || 'Failed to fetch reports');
      }

      state.totalRecords = res.total || 0;
      state.totalPages = res.pages || 1;
      state.page = res.page || 1;

      renderTable(res.data, res.page, res.per_page);
      renderPagination(res.page, res.pages, res.total);
      updateResultsCounter(res.page, res.per_page, res.total);

    } catch (err) {
      console.error('Error fetching reports:', err);
      renderErrorState(err.message);
    }
  }

  function renderLoadingTable() {
    if (!el.tableBody) return;
    el.tableBody.innerHTML = `
      <tr>
        <td colspan="13" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
          Loading AI Fitness Reports from database...
        </td>
      </tr>
    `;
  }

  function renderForbiddenState() {
    if (!el.tableBody) return;
    el.tableBody.innerHTML = `
      <tr>
        <td colspan="13" class="text-center py-5 text-danger">
          <i class="fas fa-lock fa-2x mb-2 d-block"></i>
          <strong>403 Forbidden:</strong> Access restricted strictly to Commanding Officer (CO), 2IC, or Adjutant.
        </td>
      </tr>
    `;
  }

  function renderErrorState(msg) {
    if (!el.tableBody) return;
    el.tableBody.innerHTML = `
      <tr>
        <td colspan="13" class="text-center py-5 text-danger">
          <i class="fas fa-exclamation-triangle fa-2x mb-2 d-block"></i>
          Failed to load reports: ${escapeHtml(msg)}
        </td>
      </tr>
    `;
  }

  /**
   * Renders the reports table rows with graceful N/A handling
   */
  function renderTable(rows, page, perPage) {
    if (!el.tableBody) return;

    if (!rows || rows.length === 0) {
      el.tableBody.innerHTML = `
        <tr>
          <td colspan="13">
            <div class="empty-state">
              <i class="fas fa-folder-open d-block"></i>
              <h5 class="fw-semibold">No Generated AI Fitness Reports Found</h5>
              <p class="text-muted small">No soldiers match your filter criteria or have generated reports yet.</p>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    const startIdx = (page - 1) * perPage;
    let html = '';

    rows.forEach((row, i) => {
      const sNo = startIdx + i + 1;
      const armyNo = row.army_number || 'N/A';
      const name = row.name || 'N/A';
      const rank = row.rank || 'N/A';
      const company = row.company || 'N/A';
      const age = (row.age !== null && row.age !== undefined) ? `${row.age}` : 'N/A';
      const height = (row.height_cm !== null && row.height_cm !== undefined) ? `${Number(row.height_cm).toFixed(1)} cm` : 'N/A';
      const weight = (row.actual_weight_kg !== null && row.actual_weight_kg !== undefined) ? `${Number(row.actual_weight_kg).toFixed(1)} kg` : 'N/A';
      
      // Fitness Status Badge (Unfit ONLY if overweight starting from 11%)
      const actWt = (row.actual_weight_kg !== null && row.actual_weight_kg !== undefined) ? Number(row.actual_weight_kg) : null;
      const idealWt = (row.ideal_weight_kg !== null && row.ideal_weight_kg !== undefined) ? Number(row.ideal_weight_kg) : null;
      let devPct = (row.weight_deviation_percent !== null && row.weight_deviation_percent !== undefined) ? Number(row.weight_deviation_percent) : null;
      if (devPct === null && actWt !== null && idealWt !== null && idealWt > 0) {
        devPct = Number((((actWt - idealWt) / idealWt) * 100).toFixed(2));
      }

      const isUnfit = (devPct !== null && devPct >= 11.0);
      let badgeClass = 'status-badge';
      let statusIcon = 'fa-info-circle';
      let statusDisplay = 'Healthy';

      if (actWt === null || idealWt === null || idealWt <= 0) {
        badgeClass += ' untested';
        statusIcon = 'fa-question-circle';
        statusDisplay = 'Not Tested';
      } else if (isUnfit) {
        badgeClass += ' at-risk';
        statusIcon = 'fa-times-circle';
        statusDisplay = `Unfit (+${devPct.toFixed(1)}%)`;
      } else {
        badgeClass += ' healthy';
        statusIcon = 'fa-check-circle';
        statusDisplay = devPct !== null && devPct > 0 ? `Healthy (+${devPct.toFixed(1)}%)` : 'Healthy';
      }

      // Fitness Score
      const score = (row.fitness_score !== null && row.fitness_score !== undefined) ? Number(row.fitness_score).toFixed(1) : null;
      let scoreHtml = '<span class="text-muted">N/A</span>';
      if (score !== null) {
        let scoreClass = 'score-mid';
        const num = parseFloat(score);
        if (num >= 80) scoreClass = 'score-high';
        else if (num < 60) scoreClass = 'score-low';
        scoreHtml = `<span class="score-badge ${scoreClass}">${score}</span>`;
      }

      // Report Generated & Timestamp
      const isGen = row.report_generated ? true : false;
      const genBadge = isGen 
        ? '<span class="gen-pill yes"><i class="fas fa-check"></i> Yes</span>'
        : '<span class="gen-pill no"><i class="fas fa-times"></i> No</span>';
      
      const genAt = row.generated_at_str || row.generated_at || 'N/A';

      html += `
        <tr data-army-no="${escapeHtml(armyNo)}" data-report-id="${row.id || ''}">
          <td class="text-center font-monospace">${sNo}</td>
          <td class="fw-bold font-monospace text-primary">${escapeHtml(armyNo)}</td>
          <td class="fw-semibold">${escapeHtml(name)}</td>
          <td>${escapeHtml(rank)}</td>
          <td>${escapeHtml(company)}</td>
          <td>${age}</td>
          <td>${height}</td>
          <td>${weight}</td>
          <td><span class="${badgeClass}"><i class="fas ${statusIcon}"></i> ${escapeHtml(statusDisplay)}</span></td>
          <td class="text-center">${scoreHtml}</td>
          <td class="text-center">${genBadge}</td>
          <td class="text-nowrap small text-muted">${escapeHtml(genAt)}</td>
          <td class="text-nowrap">
            <div class="action-btn-group">
              <button class="action-btn btn-view-rep" title="View Full Report (Opens Dialog)" onclick="FitnessReportsDashboard.viewReport('${escapeHtml(armyNo)}', 'tabPaneOverview')">
                <i class="fas fa-id-card me-1"></i> View Report
              </button>
            </div>
          </td>
        </tr>
      `;
    });

    el.tableBody.innerHTML = html;
  }

  function updateResultsCounter(page, perPage, total) {
    if (!el.resultsInfo) return;
    if (total === 0) {
      el.resultsInfo.textContent = 'Showing 0 records';
      return;
    }
    const start = (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, total);
    el.resultsInfo.innerHTML = `Showing <strong>${start}</strong> to <strong>${end}</strong> of <strong>${total}</strong> generated reports`;
  }

  function renderPagination(currentPage, totalPages, totalRecords) {
    if (!el.paginationNav) return;
    if (totalPages <= 1) {
      el.paginationNav.innerHTML = '';
      return;
    }

    let html = '';
    // Prev button
    html += `
      <button class="page-btn" ${currentPage <= 1 ? 'disabled' : ''} onclick="FitnessReportsDashboard.goToPage(${currentPage - 1})">
        <i class="fas fa-chevron-left"></i> Prev
      </button>
    `;

    // Numeric pages
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
      html += `<button class="page-btn" onclick="FitnessReportsDashboard.goToPage(1)">1</button>`;
      if (startPage > 2) html += `<span class="px-1 text-muted">...</span>`;
    }

    for (let p = startPage; p <= endPage; p++) {
      html += `
        <button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="FitnessReportsDashboard.goToPage(${p})">
          ${p}
        </button>
      `;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) html += `<span class="px-1 text-muted">...</span>`;
      html += `<button class="page-btn" onclick="FitnessReportsDashboard.goToPage(${totalPages})">${totalPages}</button>`;
    }

    // Next button
    html += `
      <button class="page-btn" ${currentPage >= totalPages ? 'disabled' : ''} onclick="FitnessReportsDashboard.goToPage(${currentPage + 1})">
        Next <i class="fas fa-chevron-right"></i>
      </button>
    `;

    el.paginationNav.innerHTML = html;
  }

  /**
   * Action: View Soldier Report in Modal
   */
  async function viewReport(armyNumber, initialTab = 'tabPaneOverview') {
    if (!armyNumber) return;

    // Open modal with loading state
    const m = ensureReportModalInstance();
    if (m) m.show();
    setModalLoading(armyNumber);

    try {
      const resp = await fetch(`/fitness/reports/${encodeURIComponent(armyNumber)}`);
      if (!resp.ok) throw new Error(`Could not fetch report for ${armyNumber}`);
      const data = await resp.json();

      if (!data.success) throw new Error(data.error || 'Soldier report not found');
      state.currentReportData = data;

      populateModalContent(data);
      activateModalTab(initialTab || 'tabPaneOverview');

    } catch (err) {
      console.error('Error opening report:', err);
      setModalError(err.message);
    }
  }

  function setModalLoading(armyNumber) {
    if (el.modalSoldierTitle) el.modalSoldierTitle.textContent = `Army No: ${armyNumber}`;
    if (el.modalSoldierMeta) el.modalSoldierMeta.textContent = 'Loading confidential assessment data...';
    if (el.tabContentOverview) {
      el.tabContentOverview.innerHTML = `
        <div class="text-center py-5 text-muted">
          <div class="spinner-border text-primary mb-2" role="status"></div>
          <p>Retrieving AI Fitness Report...</p>
        </div>
      `;
    }
  }

  function setModalError(msg) {
    if (el.tabContentOverview) {
      el.tabContentOverview.innerHTML = `
        <div class="alert alert-danger m-3">
          <i class="fas fa-exclamation-triangle me-2"></i> Failed to load report details: ${escapeHtml(msg)}
        </div>
      `;
    }
  }

  function activateModalTab(tabId) {
    const tabBtn = document.querySelector(`#reportModalTabs button[data-target="${tabId}"]`);
    if (tabBtn) tabBtn.click();
  }

  /**
   * Populates the multi-tab report modal
   */
  function populateModalContent(data) {
    const s = data.soldier || {};
    const pred = data.prediction || {};
    const recs = data.recommendations || {};
    const prog = data.progression || {};

    if (el.modalSoldierTitle) {
      el.modalSoldierTitle.textContent = `${s.rank || ''} ${s.name || 'Soldier'} (${s.army_number || ''})`;
    }
    if (el.modalSoldierMeta) {
      el.modalSoldierMeta.innerHTML = `
        <span><i class="fas fa-building me-1"></i> ${escapeHtml(s.company || 'Unit HQ')}</span> &bull; 
        <span><i class="fas fa-heartbeat me-1"></i> ${escapeHtml(s.medical_status || 'SHAPE-1')}</span> &bull;
        <span><i class="fas fa-clock me-1"></i> Generated: ${escapeHtml(data.generated_at || 'Just now')}</span>
      `;
    }

    if (el.modalPdfBtn) {
      el.modalPdfBtn.onclick = () => {
        if (data.report_id) {
          downloadReportPdf(data.report_id, s.army_number);
        } else {
          window.open(`/fitness/report/pdf/${encodeURIComponent(s.army_number)}`, '_blank');
        }
      };
    }

    // 1. Overview Tab
    renderModalOverview(s, pred, recs);

    // 2. Analysis Tab
    renderModalAnalysis(pred, s);

    // 3. Recommendations Tab
    renderModalRecs(recs, s);

    // 4. Progression Tab
    renderModalProgression(prog, s, pred);
  }

  function renderModalOverview(s, pred, recs) {
    if (!el.tabContentOverview) return;
    const score = pred.fitness_score !== undefined ? Number(pred.fitness_score).toFixed(1) : '--';
    const cat = pred.category_label || 'Combat Ready';
    const conf = pred.confidence !== undefined ? `${(pred.confidence * 100).toFixed(1)}%` : (pred.confidence_score ? `${pred.confidence_score}%` : '88.5%');
    const wtDiff = parseFloat(s.weight_difference_kg) || 0;
    const wtDiffStr = wtDiff > 0 ? `+${wtDiff.toFixed(1)} kg` : (wtDiff < 0 ? `${wtDiff.toFixed(1)} kg` : '0.0 kg');
    const bpetBadgeClass = s.bpet_grade === 'EXCELLENT' ? 'bg-success' : (s.bpet_grade === 'GOOD' ? 'bg-primary' : 'bg-warning text-dark');
    const pptBadgeClass = s.ppt_grade === 'EXCELLENT' ? 'bg-success' : (s.ppt_grade === 'GOOD' ? 'bg-primary' : 'bg-warning text-dark');
    const medBadgeClass = (s.has_medical_restriction || (s.medical_status && s.medical_status !== 'SHAPE-1')) ? 'bg-warning text-dark' : 'bg-success';

    el.tabContentOverview.innerHTML = `
      <div class="row g-3 mb-3 text-center">
        <div class="col-md-4">
          <div class="p-3 bg-light rounded border shadow-sm h-100">
            <div class="text-muted small text-uppercase fw-bold" style="font-size: 0.72rem;">AI Readiness Score</div>
            <div class="display-6 fw-bold text-success">${score} <span class="fs-6 text-muted">/ 100</span></div>
            <div class="badge bg-success mt-1">${escapeHtml(cat)}</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 bg-light rounded border shadow-sm h-100">
            <div class="text-muted small text-uppercase fw-bold" style="font-size: 0.72rem;">Body Composition</div>
            <div class="display-6 fw-bold text-dark">${s.bmi ? Number(s.bmi).toFixed(1) : '--'} <span class="fs-6 text-muted">BMI</span></div>
            <div class="small text-muted mt-1">${escapeHtml(s.weight_status || 'Normal Weight')} (${wtDiffStr})</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 bg-light rounded border shadow-sm h-100">
            <div class="text-muted small text-uppercase fw-bold" style="font-size: 0.72rem;">BPET / PPT Performance</div>
            <div class="mt-2 d-flex justify-content-center gap-1">
              <span class="badge ${bpetBadgeClass}">BPET: ${escapeHtml(s.bpet_grade || 'EXCELLENT')}</span>
              <span class="badge ${pptBadgeClass}">PPT: ${escapeHtml(s.ppt_grade || 'EXCELLENT')}</span>
            </div>
            <div class="small text-muted mt-1">Activity: ${escapeHtml(s.physical_activity_level || 'Moderate')}</div>
          </div>
        </div>
      </div>

      <div class="card mb-3 border shadow-sm">
        <div class="card-header bg-light fw-bold"><i class="fas fa-id-card text-primary me-2"></i> Personal &amp; Service Profile</div>
        <div class="card-body p-0">
          <table class="table table-sm table-bordered mb-0 align-middle">
            <tbody>
              <tr>
                <th class="w-25 bg-light">Army Number</th>
                <td class="fw-bold text-primary font-monospace">${escapeHtml(s.army_number || 'N/A')}</td>
                <th class="w-25 bg-light">Full Name</th>
                <td class="fw-bold">${escapeHtml(s.name || 'N/A')}</td>
              </tr>
              <tr>
                <th class="bg-light">Rank / Trade</th>
                <td>${escapeHtml(s.rank || 'N/A')} / ${escapeHtml(s.trade || 'Clk SD')}</td>
                <th class="bg-light">Company / Sec</th>
                <td>${escapeHtml(s.company || 'N/A')} / ${escapeHtml(s.section || 'CHQ')}</td>
              </tr>
              <tr>
                <th class="bg-light">Age / Total Service</th>
                <td>${s.age || 'N/A'} Yrs / ${s.service_years || 'N/A'} Yrs</td>
                <th class="bg-light">Medical Category</th>
                <td><span class="badge ${medBadgeClass}">${escapeHtml(s.medical_status || 'SHAPE-1')}</span></td>
              </tr>
              <tr>
                <th class="bg-light">Height / Actual Weight</th>
                <td>${s.height_cm || 'N/A'} cm / ${s.actual_weight_kg || 'N/A'} kg</td>
                <th class="bg-light">Ideal Reference Weight</th>
                <td>${s.ideal_weight_kg || 'N/A'} kg (Variance: <strong>${wtDiffStr}</strong>)</td>
              </tr>
              <tr>
                <th class="bg-light">Sports &amp; Physical Activity</th>
                <td colspan="3"><i class="fas fa-volleyball-ball text-primary me-1"></i> ${escapeHtml(s.sports_list || s.primary_sport || 'General Unit PT & Sports')}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderModalAnalysis(pred, s) {
    if (!el.tabContentAnalysis) return;
    const strengths = pred.key_strengths || [];
    const risks = pred.risk_factors || [];
    const confPct = pred.confidence_score ? `${pred.confidence_score}%` : (pred.confidence !== undefined ? `${(pred.confidence * 100).toFixed(1)}%` : '88.5%');
    const confNum = parseFloat(confPct) || 88.5;

    let strengthsHtml = strengths.length ? strengths.map(st => `<li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>${escapeHtml(st)}</li>`).join('') : '<li class="text-muted">Standard baseline physical strength indicators verified.</li>';
    let risksHtml = risks.length ? risks.map(rf => `<li class="mb-2"><i class="fas fa-exclamation-circle text-danger me-2"></i>${escapeHtml(rf)}</li>`).join('') : '<li class="text-muted"><i class="fas fa-shield-alt text-success me-2"></i>No adverse operational risk factors identified. Soldier is in prime combat readiness.</li>';

    el.tabContentAnalysis.innerHTML = `
      <div class="card mb-3 border-primary shadow-sm">
        <div class="card-body p-3">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="small fw-bold text-uppercase text-muted"><i class="fas fa-brain text-primary me-1"></i> AI Prediction Confidence &amp; Model Engine</span>
            <span class="fw-bold text-primary fs-5">${confPct}</span>
          </div>
          <div class="progress mb-2" style="height: 10px; border-radius: 999px;">
            <div class="progress-bar bg-primary progress-bar-striped progress-bar-animated" style="width: ${confNum}%;"></div>
          </div>
          <div class="d-flex justify-content-between text-muted small">
            <span>Model: <strong>${escapeHtml(pred.model_version || 'v1')}</strong> (${escapeHtml(pred.algorithm || 'GradientBoostingClassifier')})</span>
            <span>Safety Classification: <strong>${escapeHtml(s.medical_status || 'SHAPE-1 Cleared')}</strong></span>
          </div>
        </div>
      </div>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="card h-100 border-success shadow-sm">
            <div class="card-header bg-success text-white fw-bold">
              <i class="fas fa-thumbs-up me-2"></i> Key Strengths &amp; Positive Indicators
            </div>
            <div class="card-body">
              <ul class="list-unstyled mb-0">${strengthsHtml}</ul>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card h-100 border-warning shadow-sm">
            <div class="card-header bg-warning text-dark fw-bold">
              <i class="fas fa-exclamation-triangle me-2"></i> Operational Risk &amp; Focus Areas
            </div>
            <div class="card-body">
              <ul class="list-unstyled mb-0">${risksHtml}</ul>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function renderModalRecs(recs, s = {}) {
    if (!el.tabContentRecs) return;
    const d = recs.diet || {};
    state.currentDiet = d;
    const macros = d.macros || {};
    const ex = recs.exercise || recs.workout || {};
    const med = recs.medical_notice || {};

    // Medical notice
    const isRestricted = med.is_restricted || s.has_medical_restriction;
    const alertClass = med.alert_class || (isRestricted ? 'warning' : 'success');
    const alertIcon = isRestricted ? 'fa-exclamation-triangle text-warning' : 'fa-shield-alt text-success';
    const alertTitle = med.title || (isRestricted ? 'Medical Restrictions Apply' : 'Medically Cleared (SHAPE-1)');
    const alertMsg = med.message || (isRestricted ? (s.restrictions || 'Soldier has active physical activity restrictions.') : 'Soldier is medically cleared for standard military physical training and advanced tactical conditioning.');

    // Diet info
    const targetCals = d.target_calories || d.calories_target || 2400;
    const strategy = d.strategy || 'Maintenance Calorie Plan tailored for sustained military operational stamina and SHAPE-1 preservation.';
    const messCat = d.mess_category || (['SUBEDAR', 'SUBEDAR MAJOR', 'NAIB SUBEDAR', 'NB SUB', 'SUB', 'SUB MAJ'].some(r => (s.rank || '').toUpperCase().includes(r)) ? 'JCO MESS' : 'OR MESS');
    const dayOfWeek = d.day_of_week || '';
    const estIntake = d.estimated_intake || {};
    const optionalDiet = d.optional_diet_plan || null;
    const proteinVal = macros.protein_grams ? `${macros.protein_grams}g (${macros.protein_pct || 20}%)` : (d.protein_g ? `${d.protein_g} (20%)` : '120g (20%)');
    const carbVal = macros.carb_grams ? `${macros.carb_grams}g (${macros.carb_pct || 55}%)` : (d.carbs_g ? `${d.carbs_g} (55%)` : '300g (55%)');
    const fatVal = macros.fat_grams ? `${macros.fat_grams}g (${macros.fat_pct || 25}%)` : (d.fat_g ? `${d.fat_g} (25%)` : '60g (25%)');
    const hydrationVal = d.hydration_liters ? `${d.hydration_liters} Liters / Day` : '3.5 Liters / Day';

    // Sample Menu rows fallback
    const sampleMenu = d.sample_menu || [];

    // Exercise table
    const exTitle = ex.title || 'Structured Tactical Regimen';
    const exFocus = ex.focus_area || ex.focus || 'Cardiovascular endurance, core strength, and tactical obstacle mobility.';
    let exercisesList = Array.isArray(ex.exercises) && ex.exercises.length > 0 ? ex.exercises : [
      { exercise: '5km Tactical Interval Run', sets: '1', reps: '5km', duration: '28-30 min', frequency: '3 days/week', intensity: 'Moderate', rest: '90s rest' },
      { exercise: 'Push-ups & Chin-ups Complex', sets: '4', reps: '20-25 / 8-10 reps', duration: '15 min', frequency: '4 days/week', intensity: 'High', rest: '60s rest' },
      { exercise: 'Core Conditioning (Planks & Sit-ups)', sets: '3', reps: '60s hold / 30 reps', duration: '12 min', frequency: '4 days/week', intensity: 'Moderate', rest: '45s rest' },
      { exercise: 'Military Obstacle Course Traverse', sets: '2', reps: '1 circuit', duration: '20 min', frequency: '2 days/week', intensity: 'High', rest: '90s rest' },
      { exercise: 'Tactical Mobility & Stretching', sets: '1', reps: 'Full Body', duration: '15 min', frequency: 'Daily (Post-PT)', intensity: 'Low', rest: '30s rest' }
    ];

    const exRowsHtml = exercisesList.map(item => {
      let badgeClass = 'bg-primary';
      if (item.intensity === 'High') badgeClass = 'bg-danger';
      else if (item.intensity === 'Low' || item.intensity === 'Recovery') badgeClass = 'bg-info text-dark';
      return `
        <tr>
          <td class="fw-bold ps-3">
            ${escapeHtml(item.exercise || '')}
            ${item.progression_note ? `<div class="small text-muted fst-italic mt-0.5"><i class="fas fa-level-up-alt text-primary me-1"></i>${escapeHtml(item.progression_note)}</div>` : ''}
          </td>
          <td>${escapeHtml(String(item.sets || '--'))}</td>
          <td>${escapeHtml(String(item.reps || '--'))}</td>
          <td>${escapeHtml(String(item.duration || '--'))}</td>
          <td>${escapeHtml(String(item.frequency || '--'))}</td>
          <td><span class="badge ${badgeClass}">${escapeHtml(item.intensity || 'Moderate')}</span></td>
          <td class="pe-3 small text-muted text-nowrap">${escapeHtml(item.rest || '60s rest')}</td>
        </tr>
      `;
    }).join('');

    // Blocked exercises if any
    let blockedHtml = '';
    if (Array.isArray(ex.blocked_exercises) && ex.blocked_exercises.length > 0) {
      blockedHtml = `
        <div class="alert alert-warning mt-3 mb-0">
          <h6 class="fw-bold mb-1"><i class="fas fa-ban me-1"></i> Contraindicated Exercises Blocked by Safety Engine:</h6>
          <ul class="mb-0 small ps-3">
            ${ex.blocked_exercises.map(b => `<li><strong>${escapeHtml(b.exercise || '')}:</strong> ${escapeHtml(b.reason || 'Restricted per medical status.')}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    el.tabContentRecs.innerHTML = `
      <div>
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
          <h5 class="fw-bold text-dark mb-0">
            <i class="fas fa-heartbeat text-danger me-2"></i> Personalized Diet &amp; Tactical Exercise Recommendations
          </h5>
          <div class="d-flex align-items-center gap-2">
            <span class="badge ${messCat === 'JCO MESS' ? 'bg-warning text-dark' : 'bg-success'} px-3 py-1.5" style="border-radius: 999px;">
              <i class="fas fa-concierge-bell me-1"></i> ${escapeHtml(messCat)} ${dayOfWeek ? `&bull; ${escapeHtml(dayOfWeek)}` : ''}
            </span>
            <span class="badge bg-primary px-3 py-1.5" style="border-radius: 999px;">AI Tailored</span>
          </div>
        </div>

        <!-- Medical Safety Banner -->
        <div class="alert alert-${alertClass} d-flex align-items-center mb-4 py-2.5 px-3">
          <i class="fas ${alertIcon} fa-2x me-3"></i>
          <div>
            <h6 class="fw-bold mb-1">${escapeHtml(alertTitle)}</h6>
            <p class="mb-0 small">${escapeHtml(alertMsg)}</p>
          </div>
        </div>

        <!-- 1. NUTRITION SECTION -->
        <div class="mb-4">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h6 class="fw-bold text-primary mb-0">
              <i class="fas fa-utensils me-2"></i> Targeted Nutrition &amp; Macronutrient Plan
            </h6>
            <span class="badge bg-primary px-3 py-2 fs-6 font-monospace shadow-sm" style="border-radius: 999px;">${targetCals} kcal</span>
          </div>

          <div class="p-3 border rounded mb-3" style="background: #f8fafc;">
            <div class="small text-muted fw-bold text-uppercase mb-1" style="font-size: 0.73rem; letter-spacing: 0.5px;">CALORIC STRATEGY</div>
            <div class="fw-bold text-dark" style="font-size: 0.95rem;">${escapeHtml(strategy)}</div>
          </div>

          ${estIntake && estIntake.total_calories ? `
          <div class="row g-2 mb-3">
            <div class="col-md-6">
              <div class="p-2 px-3 border rounded bg-white small d-flex justify-content-between">
                <span class="text-muted">Target Calories: <strong>${targetCals} kcal</strong></span>
                <span class="text-muted">Est. Mess Intake: <strong class="text-primary">${estIntake.total_calories} kcal</strong></span>
              </div>
            </div>
            <div class="col-md-6">
              <div class="p-2 px-3 border rounded bg-white small d-flex justify-content-between">
                <span class="text-muted">Target Protein: <strong>${macros.protein_grams || 105}g</strong></span>
                <span class="text-muted">Est. Mess Protein: <strong class="text-success">${estIntake.total_protein_g || 0}g</strong></span>
              </div>
            </div>
          </div>
          ` : ''}

          <div class="row g-3 mb-4 text-center">
            <div class="col-md-3 col-6">
              <div class="p-3 border rounded bg-white shadow-sm h-100">
                <div class="small text-muted fw-bold text-uppercase" style="font-size: 0.72rem;">DAILY PROTEIN</div>
                <div class="fw-bold my-1" style="color: #3b82f6; font-size: 1.35rem;">${escapeHtml(proteinVal)}</div>
                <div class="small text-muted" style="font-size: 0.75rem;">Muscle Recovery &amp; Repair</div>
              </div>
            </div>
            <div class="col-md-3 col-6">
              <div class="p-3 border rounded bg-white shadow-sm h-100">
                <div class="small text-muted fw-bold text-uppercase" style="font-size: 0.72rem;">COMPLEX CARBS</div>
                <div class="fw-bold my-1" style="color: #10b981; font-size: 1.35rem;">${escapeHtml(carbVal)}</div>
                <div class="small text-muted" style="font-size: 0.75rem;">Endurance Energy</div>
              </div>
            </div>
            <div class="col-md-3 col-6">
              <div class="p-3 border rounded bg-white shadow-sm h-100">
                <div class="small text-muted fw-bold text-uppercase" style="font-size: 0.72rem;">HEALTHY FATS</div>
                <div class="fw-bold my-1" style="color: #f59e0b; font-size: 1.35rem;">${escapeHtml(fatVal)}</div>
                <div class="small text-muted" style="font-size: 0.75rem;">Hormonal Balance</div>
              </div>
            </div>
            <div class="col-md-3 col-6">
              <div class="p-3 border rounded bg-white shadow-sm h-100">
                <div class="small text-muted fw-bold text-uppercase" style="font-size: 0.72rem;">DAILY HYDRATION</div>
                <div class="fw-bold my-1" style="color: #06b6d4; font-size: 1.35rem;">${escapeHtml(hydrationVal)}</div>
                <div class="small text-muted" style="font-size: 0.75rem;">Outdoor PT Perspiration</div>
              </div>
            </div>
          </div>

          <!-- Structured Meal Menu Table with 30-Day Weekly Schedule -->
          <div class="p-3 border rounded mb-3" style="background: #f8fafc;">
            <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
              <div>
                <h6 class="fw-bold text-dark mb-1"><i class="fas fa-calendar-alt text-primary me-1"></i> Official ${escapeHtml(messCat)} 30-Day Nutrition Schedule</h6>
                <div class="small text-muted">Weekly Cycle (Monday &ndash; Sunday) &bull; Calibrated Serving Portions</div>
              </div>
              <div class="d-flex align-items-center gap-2">
                <span class="badge ${messCat === 'JCO MESS' ? 'bg-warning text-dark' : 'bg-success'} px-3 py-1.5">${escapeHtml(messCat)}</span>
                <span class="badge bg-primary px-3 py-1.5">30-Day Plan</span>
              </div>
            </div>

            <!-- Simple Table of Full Week Nutrition Schedule -->
            <div class="table-responsive" id="dashMessMenuContainer">
              <!-- Populated by switchMessDay -->
            </div>
          </div>

          ${Array.isArray(d.roadmap_30d) && d.roadmap_30d.length > 0 ? `
          <div class="p-3 border rounded mb-3" style="background: #f8fafc;">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <h6 class="fw-bold text-dark mb-0"><i class="fas fa-route text-success me-1"></i> 30-Day Nutrition Progression Roadmap (4-Week Cycle)</h6>
              <span class="badge bg-secondary">30-Day Target</span>
            </div>
            <div class="row g-2 pt-2">
              ${d.roadmap_30d.map(w => `
                <div class="col-md-6 col-lg-3">
                  <div class="p-2.5 border rounded bg-white h-100 shadow-sm" style="font-size: 0.8rem;">
                    <div class="fw-bold text-primary mb-1">${escapeHtml(w.week)}: ${escapeHtml(w.phase)}</div>
                    <div class="small text-dark mb-1"><strong>Focus:</strong> ${escapeHtml(w.focus)}</div>
                    <div class="small text-success mb-1"><strong>Strategy:</strong> ${escapeHtml(w.mess_strategy || '')}</div>
                    <div class="small text-muted"><strong>Target:</strong> ${escapeHtml(w.milestone)}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
          ` : ''}

          ${optionalDiet && optionalDiet.items && optionalDiet.items.length > 0 ? `
          <div class="p-3 border rounded mb-4" style="background: #fdfbf7; border-color: #f6d365 !important;">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <h6 class="fw-bold text-dark mb-0"><i class="fas fa-apple-alt text-warning me-2"></i> ${escapeHtml(optionalDiet.title || 'Optional Supplementary Diet Plan')}</h6>
              <span class="badge bg-secondary">Optional Supplement</span>
            </div>
            <p class="small text-muted mb-2">${escapeHtml(optionalDiet.description || 'Supplementary conditioning plan for voluntary optimization outside mandatory mess hours.')}</p>
            <div class="table-responsive">
              <table class="table table-sm table-borderless mb-0">
                <tbody>
                  ${(optionalDiet.items || []).map(it => `
                    <tr>
                      <td class="fw-bold text-nowrap text-secondary" style="width: 28%;">${escapeHtml(it.time || '')}</td>
                      <td class="text-dark"><strong>${escapeHtml(it.item || '')}</strong> &mdash; ${escapeHtml(it.quantity || '')} <span class="text-muted small">(${escapeHtml(it.purpose || '')})</span></td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          ` : ''}
        </div>

        <hr class="my-4">

        <!-- 2. TACTICAL EXERCISE SECTION -->
        <div>
          <div class="d-flex align-items-center justify-content-between mb-2">
            <h6 class="fw-bold text-primary mb-0">
              <i class="fas fa-running me-2"></i> Structured Tactical Physical Training Regimen
            </h6>
            <span class="badge bg-dark px-3 py-2 shadow-sm">${escapeHtml(exTitle)}</span>
          </div>
          <div class="small text-muted mb-3">${escapeHtml(exFocus)}</div>

          <div class="table-responsive border rounded mb-3">
            <table class="table table-sm table-hover mb-0 align-middle">
              <thead class="table-light">
                <tr>
                  <th class="ps-3">Exercise / Drill</th>
                  <th>Sets</th>
                  <th>Reps / Volume</th>
                  <th>Duration</th>
                  <th>Frequency</th>
                  <th>Intensity</th>
                  <th class="pe-3">Rest Interval</th>
                </tr>
              </thead>
              <tbody>
                ${exRowsHtml}
              </tbody>
            </table>
          </div>

          ${blockedHtml}
        </div>
      </div>
    `;

    // Default to Full Week Plan
    switchMessDay('full');
  }

  function renderModalProgression(prog, s = {}, pred = {}) {
    if (!el.tabContentProgression) return;
    const ms = Array.isArray(prog.milestones) ? prog.milestones : [];
    const cd = prog.chart_data || {};
    const wSeries = cd.weight_series || [];
    const sSeries = cd.score_series || [];
    const bmiSeries = cd.bmi_series || [];

    const curWt = parseFloat(s.actual_weight_kg) || 70.0;
    const idealWt = parseFloat(s.ideal_weight_kg) || curWt;
    const curHt = parseFloat(s.height_cm) || 170.0;
    const curScore = parseFloat(pred.fitness_score) || 70.0;
    const curBmi = parseFloat(s.bmi) || (curHt > 0 ? (curWt / ((curHt / 100.0) ** 2)) : 23.5);

    // Safe calculated fallback trajectories based on military standards
    const excess = curWt - idealWt;
    let defW30 = curWt, defW60 = curWt, defW90 = curWt;
    if (excess > 0) {
      defW30 = +(curWt - Math.min(1.8, excess * 0.35)).toFixed(1);
      defW60 = +(curWt - Math.min(3.5, excess * 0.70)).toFixed(1);
      defW90 = +(curWt - Math.min(5.0, excess * 0.95)).toFixed(1);
    } else if (excess < 0) {
      const deficit = Math.abs(excess);
      defW30 = +(curWt + Math.min(1.2, deficit * 0.35)).toFixed(1);
      defW60 = +(curWt + Math.min(2.4, deficit * 0.70)).toFixed(1);
      defW90 = +(curWt + Math.min(3.5, deficit * 0.90)).toFixed(1);
    }

    const t30 = prog.trajectory_30d || {};
    const t60 = prog.trajectory_60d || {};
    const t90 = prog.trajectory_90d || {};

    const score30 = t30.projected_fitness_score || ms[1]?.fitness_score || sSeries[1] || Math.min(100, Math.round(curScore + (100 - curScore) * 0.25));
    const score60 = t60.projected_fitness_score || ms[2]?.fitness_score || sSeries[2] || Math.min(100, Math.round(curScore + (100 - curScore) * 0.55));
    const score90 = t90.projected_fitness_score || ms[3]?.fitness_score || sSeries[3] || Math.min(100, Math.round(curScore + (100 - curScore) * 0.85));

    const wt30 = t30.projected_weight_kg || t30.weight_kg || ms[1]?.weight_kg || wSeries[1] || defW30;
    const wt60 = t60.projected_weight_kg || t60.weight_kg || ms[2]?.weight_kg || wSeries[2] || defW60;
    const wt90 = t90.projected_weight_kg || t90.weight_kg || ms[3]?.weight_kg || wSeries[3] || defW90;

    const bmi30 = t30.projected_bmi || t30.bmi || ms[1]?.bmi || bmiSeries[1] || (curHt > 0 ? +(wt30 / ((curHt / 100.0) ** 2)).toFixed(1) : curBmi);
    const bmi60 = t60.projected_bmi || t60.bmi || ms[2]?.bmi || bmiSeries[2] || (curHt > 0 ? +(wt60 / ((curHt / 100.0) ** 2)).toFixed(1) : curBmi);
    const bmi90 = t90.projected_bmi || t90.bmi || ms[3]?.bmi || bmiSeries[3] || (curHt > 0 ? +(wt90 / ((curHt / 100.0) ** 2)).toFixed(1) : curBmi);

    const bpet30 = ms[1]?.bpet_target || 'Improved 5km pace & aerobic stamina';
    const bpet60 = ms[2]?.bpet_target || 'Enhanced obstacle agility & tempo';
    const bpet90 = ms[3]?.bpet_target || 'Peak tactical BPET combat readiness';

    el.tabContentProgression.innerHTML = `
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-light fw-bold">
          <i class="fas fa-chart-line me-2 text-primary"></i> 30-60-90 Day Tactical Readiness Trajectory
        </div>
        <div class="card-body">
          <div class="row g-3 text-center mb-3">
            <div class="col-md-4">
              <div class="p-3 border rounded bg-white shadow-sm">
                <span class="badge bg-secondary mb-2">30 Days</span>
                <div class="fs-4 fw-bold text-primary">${score30} PTS</div>
                <div class="fw-semibold text-dark mt-1" style="font-size: 0.95rem;">Weight: ${Number(wt30).toFixed(1)} kg</div>
                <div class="small text-muted">BMI: ${Number(bmi30).toFixed(1)}</div>
                <div class="small text-muted mt-2 border-top pt-2" style="font-size: 0.78rem;">
                  <i class="fas fa-running text-primary me-1"></i>${escapeHtml(bpet30)}
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="p-3 border rounded bg-white shadow-sm">
                <span class="badge bg-info text-dark mb-2">60 Days</span>
                <div class="fs-4 fw-bold text-info">${score60} PTS</div>
                <div class="fw-semibold text-dark mt-1" style="font-size: 0.95rem;">Weight: ${Number(wt60).toFixed(1)} kg</div>
                <div class="small text-muted">BMI: ${Number(bmi60).toFixed(1)}</div>
                <div class="small text-muted mt-2 border-top pt-2" style="font-size: 0.78rem;">
                  <i class="fas fa-running text-info me-1"></i>${escapeHtml(bpet60)}
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="p-3 border rounded bg-white shadow-sm">
                <span class="badge bg-success mb-2">90 Days (Target)</span>
                <div class="fs-4 fw-bold text-success">${score90} PTS</div>
                <div class="fw-semibold text-dark mt-1" style="font-size: 0.95rem;">Weight: ${Number(wt90).toFixed(1)} kg</div>
                <div class="small text-muted">BMI: ${Number(bmi90).toFixed(1)}</div>
                <div class="small text-muted mt-2 border-top pt-2" style="font-size: 0.78rem;">
                  <i class="fas fa-medal text-success me-1"></i>${escapeHtml(bpet90)}
                </div>
              </div>
            </div>
          </div>
          <div class="alert alert-light border py-2 px-3 mb-0 small text-muted d-flex align-items-center justify-content-between">
            <span><i class="fas fa-info-circle text-primary me-1"></i> Baseline: <strong>${Number(curWt).toFixed(1)} kg</strong> &bull; Target Reference: <strong>${Number(idealWt).toFixed(1)} kg</strong></span>
            <span class="badge bg-light text-dark border">Standard Military Progression</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Action: Download Saved Report PDF
   */
  function downloadReportPdf(reportId, armyNumber) {
    if (reportId && reportId > 0) {
      window.open(`/fitness/reports/${reportId}/pdf`, '_blank');
    } else if (armyNumber) {
      window.open(`/fitness/report/pdf/${encodeURIComponent(armyNumber)}`, '_blank');
    }
  }

  /**
   * Action: Regenerate Report (Forces Recalculation)
   */
  async function regenerateReport(armyNumber) {
    if (!armyNumber) return;
    const confirmed = window.confirm(`Force recalculate AI Fitness Report for Army Number "${armyNumber}"?\nThis will re-run the AI prediction and update the saved record.`);
    if (!confirmed) return;

    // Show row loading indicator
    const tr = document.querySelector(`tr[data-army-no="${armyNumber}"]`);
    let origHtml = '';
    if (tr) {
      origHtml = tr.innerHTML;
      tr.innerHTML = `<td colspan="13" class="text-center py-3 text-primary"><div class="spinner-border spinner-border-sm me-2"></div> Recalculating AI prediction for ${escapeHtml(armyNumber)}...</td>`;
    }

    try {
      const resp = await fetch('/fitness/api/reports/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ army_number: armyNumber, goal: 'Overall Fitness' })
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const res = await resp.json();

      if (!res.success) throw new Error(res.error || 'Failed to regenerate report');

      // Refresh table and dynamic stats
      loadDashboardStats();
      loadReportsData();

    } catch (err) {
      console.error('Regenerate error:', err);
      alert(`Error regenerating report: ${err.message}`);
      if (tr && origHtml) tr.innerHTML = origHtml;
    }
  }

  function goToPage(pageNum) {
    if (pageNum < 1 || pageNum > state.totalPages) return;
    state.page = pageNum;
    loadReportsData();
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function exportDirectoryPdf() {
    const params = new URLSearchParams({
      search: state.search,
      company: state.company,
      status: state.status,
      from_date: state.fromDate,
      to_date: state.toDate,
      download: '1'
    });
    window.open(`/fitness/api/reports/export-pdf?${params.toString()}`, '_blank');
  }

  function switchMessDay(dayName) {
    if (!state.currentDiet) return;
    const weeklySched = state.currentDiet.weekly_schedule || {};
    const activeDay = state.currentDiet.day_of_week || 'Monday';

    // Update active pill button
    const container = document.getElementById('dashMessDayTabs');
    if (container) {
      container.querySelectorAll('.dash-mess-day-pill').forEach(btn => {
        if ((btn.getAttribute('data-day') || '').toLowerCase() === (dayName || '').toLowerCase()) {
          btn.classList.add('btn-primary', 'active');
          btn.classList.remove('btn-outline-primary');
        } else {
          btn.classList.remove('btn-primary', 'active');
          btn.classList.add('btn-outline-primary');
        }
      });
    }

    const targetContainer = document.getElementById('dashMessMenuContainer');
    if (!targetContainer) return;

    if ((dayName || '').toLowerCase() === 'full') {
      const sol = currentSoldierData || {};
      const rep = currentReportData || {};
      const isJc = (sol.rank && ['SUBEDAR', 'SUB', 'NB SUB', 'HONY', 'HONORARY'].some(r => sol.rank.toUpperCase().includes(r))) ||
                   (sol.army_number && sol.army_number.toUpperCase().includes('JC')) ||
                   (rep.nutrition && (rep.nutrition.mess_category || '').toUpperCase().includes('JCO'));

      const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      const rows = days.map((dName, idx) => {
        const dData = weeklySched[dName] || {};
        const isToday = (activeDay && dName.toLowerCase() === activeDay.toLowerCase());
        const meals = dData.meals || {};
        const getMealText = (mKey) => {
          const items = meals[mKey] || [];
          if (!Array.isArray(items) || items.length === 0) {
            return '<span class="text-muted small fst-italic">--</span>';
          }
          return items.map(it => {
            const name = typeof it === 'string' ? it : (it.food_item || it.item || 'Item');
            const portion = typeof it === 'string' ? '' : (it.portion || it.quantity || '');
            return `
              <div class="d-flex align-items-center justify-content-between gap-1 py-1 mb-1 border-bottom" style="border-bottom-style: dashed !important; font-size: 0.81rem;">
                <span class="fw-bold text-dark">${escapeHtml(name)}</span>
                <span class="badge bg-white text-primary border border-primary-subtle fw-bold font-monospace shadow-xs px-2 py-0.5" style="font-size: 0.76rem; white-space: nowrap;">
                  ${escapeHtml(portion)}
                </span>
              </div>
            `;
          }).join('');
        };

        return `
          <tr>
            <td class="ps-3 align-top">
              <div class="fw-bold text-dark">${dName}</div>
              <div class="small text-muted font-monospace" style="font-size: 0.75rem;">Day ${idx + 1}</div>
            </td>
            <td class="align-top" style="font-size: 0.82rem;">${getMealText('Breakfast')}</td>
            ${!isJc ? `<td class="align-top" style="font-size: 0.82rem;">${getMealText('Tea')}</td>` : ''}
            <td class="align-top" style="font-size: 0.82rem;">${getMealText('Lunch')}</td>
            <td class="align-top pe-3" style="font-size: 0.82rem;">${getMealText('Dinner')}</td>
          </tr>
        `;
      }).join('');

      targetContainer.innerHTML = `
        <table class="table table-sm table-bordered table-hover mb-0 align-middle shadow-sm" style="background: #ffffff;">
          <thead class="table-light">
            <tr style="font-size: 0.82rem;">
              <th style="width: ${isJc ? '15%' : '14%'};" class="ps-3 text-uppercase text-muted">Day</th>
              <th style="width: ${isJc ? '27%' : '22%'};" class="text-uppercase text-primary"><i class="fas fa-sun text-warning me-1"></i> Breakfast</th>
              ${!isJc ? `<th style="width: 18%;" class="text-uppercase text-secondary"><i class="fas fa-mug-hot text-secondary me-1"></i> Tea</th>` : ''}
              <th style="width: ${isJc ? '29%' : '23%'};" class="text-uppercase text-success"><i class="fas fa-drumstick-bite text-success me-1"></i> Lunch</th>
              <th style="width: ${isJc ? '29%' : '23%'}; color: #4f46e5;" class="pe-3 text-uppercase"><i class="fas fa-moon me-1" style="color: #4f46e5;"></i> Dinner</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    } else {
      const dData = weeklySched[dayName] || weeklySched['Monday'] || {};
      const meals = dData.meals || {};
      const order = ['Breakfast', 'Tea', 'Lunch', 'Dinner'];
      const mealKeys = Object.keys(meals).sort((a, b) => {
        const idxA = order.indexOf(a);
        const idxB = order.indexOf(b);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.localeCompare(b);
      });

      let rowsHtml = '';
      if (mealKeys.length > 0) {
        rowsHtml = mealKeys.map(k => {
          const items = (meals[k] || []).map(it => `${escapeHtml(it.food_item)}: ${escapeHtml(it.portion)}`).join(' + ');
          return `
            <tr>
              <td class="fw-bold text-nowrap text-primary ps-3" style="width: 22%; font-size: 0.88rem;">${k} (${dayName})</td>
              <td class="pe-3" style="font-size: 0.88rem;">${items}</td>
            </tr>
          `;
        }).join('');
      } else if (Array.isArray(dData.sample_menu) && dData.sample_menu.length > 0) {
        rowsHtml = dData.sample_menu.map(m => `
          <tr>
            <td class="fw-bold text-nowrap text-primary ps-3" style="width: 22%; font-size: 0.88rem;">${escapeHtml(m.meal)}</td>
            <td class="pe-3" style="font-size: 0.88rem;">${escapeHtml(m.items)}</td>
          </tr>
        `).join('');
      }

      targetContainer.innerHTML = `
        <table class="table table-sm table-hover table-borderless mb-0 align-middle" style="background: #ffffff;">
          <tbody>${rowsHtml}</tbody>
        </table>
      `;
    }
  }

  // Public Interface for Inline HTML Onclick Handlers
  window.FitnessReportsDashboard = {
    viewReport,
    downloadReportPdf,
    regenerateReport,
    filterByStatus,
    goToPage,
    exportDirectoryPdf,
    switchMessDay
  };

})();
