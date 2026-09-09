/**
 * UMS - AI/ML Individual Fitness Trend & Personalized Report JavaScript Controller
 * Handles interactive 6-stage workflow, search, charts, API calls, and PDF exports.
 */

class FitnessTrendApp {
  constructor() {
    this.currentArmyNumber = null;
    this.currentData = null;
    this.activeStage = 'profile';
    this.currentGoal = 'Overall Fitness';
    this.currentLang = 'en';
    this.charts = {};
    
    this.initElements();
    this.bindEvents();
    this.loadInitialSearch();
  }

  initElements() {
    this.searchInput = document.getElementById('fitnessSearchInput');
    this.searchResults = document.getElementById('searchResultsDropdown');
    this.clearBtn = document.getElementById('clearSearchBtn');
    this.pdfBtn = document.getElementById('downloadPdfBtn');
    this.previewBtn = document.getElementById('previewPdfBtn');
    this.viewPdfBtn = document.getElementById('viewPdfBtn');
    this.savePdfBtn = document.getElementById('savePdfBtn');
    this.pdfSuccessActions = document.getElementById('pdfSuccessActions');
    this.pdfSuccessFileName = document.getElementById('pdfSuccessFileName');
    this.goalSelect = document.getElementById('fitnessGoalSelect');
    this.langSelect = document.getElementById('fitnessLangSelect');
    this.stageNav = document.getElementById('workflowStageNav');
    this.activeSearchIndex = -1;
    this.latestPdfBlob = null;
    this.latestPdfFilename = null;
    
    // Total Count Badge Elements
    this.totalPersonnelCount = document.getElementById('totalPersonnelCount');
    this.searchCardTotalCount = document.getElementById('searchCardTotalCount');
    this.welcomeTotalCount = document.getElementById('welcomeTotalCount');

    // Ensure export & preview buttons are disabled initially
    if (this.pdfBtn) this.pdfBtn.disabled = true;
    if (this.previewBtn) this.previewBtn.disabled = true;
    
    // Main Content Containers
    this.welcomeState = document.getElementById('fitnessWelcomeState');
    this.loadingState = document.getElementById('fitnessLoadingState');
    this.activeContent = document.getElementById('fitnessActiveContent');
    this.errorAlert = document.getElementById('fitnessErrorAlert');
    
    // Stage view wrappers
    this.stageViews = {
      profile: document.getElementById('stageViewProfile'),
      analysis: document.getElementById('stageViewAnalysis'),
      prediction: document.getElementById('stageViewPrediction'),
      recommendations: document.getElementById('stageViewRecommendations'),
      progression: document.getElementById('stageViewProgression'),
      report: document.getElementById('stageViewReport')
    };
  }

  bindEvents() {
    // Search input with debounce
    let debounceTimer;
    this.searchInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (this.clearBtn) {
        if (val) this.clearBtn.classList.remove('d-none');
        else this.clearBtn.classList.add('d-none');
      }

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        this.performSearch(val, true);
      }, 200);
    });

    this.searchInput.addEventListener('focus', () => {
      const currentVal = this.searchInput.value.trim();
      this.performSearch(currentVal, true);
    });

    // Keyboard navigation in search results
    this.searchInput.addEventListener('keydown', (e) => {
      const items = this.searchResults.querySelectorAll('.search-item');
      if (items.length === 0 || this.searchResults.classList.contains('d-none')) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.activeSearchIndex = (this.activeSearchIndex + 1) % items.length;
        this.updateActiveSearchItem(items);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.activeSearchIndex = (this.activeSearchIndex - 1 + items.length) % items.length;
        this.updateActiveSearchItem(items);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (this.activeSearchIndex >= 0 && items[this.activeSearchIndex]) {
          items[this.activeSearchIndex].click();
        }
      } else if (e.key === 'Escape') {
        this.searchResults.classList.add('d-none');
        this.activeSearchIndex = -1;
      }
    });

    // Clear search button
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.searchInput.value = '';
        this.clearBtn.classList.add('d-none');
        this.searchResults.innerHTML = '';
        this.performSearch('', true);
        this.currentArmyNumber = null;
        this.currentData = null;
        if (this.pdfBtn) this.pdfBtn.disabled = true;
        if (this.previewBtn) this.previewBtn.disabled = true;
        if (this.pdfSuccessActions) this.pdfSuccessActions.classList.add('d-none');
        this.activeContent.classList.add('d-none');
        this.errorAlert.classList.add('d-none');
        this.welcomeState.classList.remove('d-none');
        this.searchInput.focus();
      });
    }

    // Close search dropdown when clicked outside
    document.addEventListener('click', (e) => {
      if (!this.searchInput.contains(e.target) && !this.searchResults.contains(e.target)) {
        this.searchResults.classList.add('d-none');
        this.activeSearchIndex = -1;
      }
    });

    // Goal change
    if (this.goalSelect) {
      this.goalSelect.addEventListener('change', (e) => {
        this.currentGoal = e.target.value;
        if (this.currentArmyNumber) {
          this.loadAnalysis(this.currentArmyNumber, this.currentGoal);
        }
      });
    }

    // Language change
    if (this.langSelect) {
      this.langSelect.addEventListener('change', (e) => {
        this.currentLang = e.target.value;
        if (this.currentArmyNumber) {
          this.loadAnalysis(this.currentArmyNumber, this.currentGoal);
        }
      });
    }

    // Workflow tabs
    if (this.stageNav) {
      this.stageNav.querySelectorAll('.workflow-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const stage = btn.getAttribute('data-stage');
          this.switchStage(stage);
        });
      });
    }

    // Preview Report button (opens printable HTML view in new tab)
    if (this.previewBtn) {
      this.previewBtn.addEventListener('click', () => {
        if (!this.currentArmyNumber) return;
        const lang = this.currentLang || (this.langSelect ? this.langSelect.value : 'en');
        const goal = this.currentGoal || (this.goalSelect ? this.goalSelect.value : 'Overall Fitness');
        const previewUrl = `/fitness/report/preview/${encodeURIComponent(this.currentArmyNumber)}?lang=${encodeURIComponent(lang)}&goal=${encodeURIComponent(goal)}`;
        window.open(previewUrl, '_blank');
      });
    }

    // PDF Download button with status notifications & Action Bar
    const pdfBtn = this.pdfBtn || document.getElementById('downloadPdfBtn');
    const statusAlert = document.getElementById('pdfExportStatusAlert');
    const statusSpinner = document.getElementById('pdfExportSpinner');
    const successIcon = document.getElementById('pdfExportSuccessIcon');
    const statusText = document.getElementById('pdfExportStatusText');

    if (pdfBtn) {
      pdfBtn.addEventListener('click', async () => {
        if (!this.currentArmyNumber) return;

        const lang = this.currentLang || (this.langSelect ? this.langSelect.value : 'en');
        const langName = this.langSelect && this.langSelect.selectedIndex >= 0
          ? this.langSelect.options[this.langSelect.selectedIndex].text
          : 'English';

        const originalHtml = pdfBtn.innerHTML;
        pdfBtn.disabled = true;
        if (this.previewBtn) this.previewBtn.disabled = true;
        pdfBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Generating...`;

        // Display "Generating <Language> report..."
        if (statusAlert) {
          statusAlert.className = 'alert alert-info py-2 px-3 rounded-3 mb-3 d-flex align-items-center gap-2 shadow-sm';
          statusAlert.classList.remove('d-none');
          if (statusSpinner) statusSpinner.classList.remove('d-none');
          if (successIcon) successIcon.classList.add('d-none');
          if (statusText) statusText.textContent = `Generating ${langName} report...`;
        }

        try {
          const exportPayload = {
            army_number: this.currentArmyNumber,
            language: lang,
            goal: this.currentGoal
          };

          // Try canonical blueprint route first, fallback to aliases
          let res = await fetch('/fitness/report/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(exportPayload)
          });

          if (!res.ok && res.status === 404) {
            res = await fetch('/fitness/api/export-pdf', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(exportPayload)
            });
          }

          if (!res.ok && res.status === 404) {
            res = await fetch('/api/fitness-trend/export-pdf', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(exportPayload)
            });
          }

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP ${res.status}: Failed to generate ${langName} report.`);
          }

          const blob = await res.blob();
          this.latestPdfBlob = blob;
          
          // Determine filename from header or fallback
          const contentDisposition = res.headers.get('Content-Disposition');
          const todayStr = new Date().toISOString().slice(0,10).replace(/-/g,'');
          let filename = `UMS_Fitness_Report_${this.currentArmyNumber}_${lang.toUpperCase()}_${todayStr}.pdf`;
          if (contentDisposition && contentDisposition.includes('filename=')) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/);
            if (match && match[1]) filename = match[1];
          }
          this.latestPdfFilename = filename;

          // Trigger automatic download
          const downloadUrl = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.setAttribute('download', filename);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(downloadUrl);

          // Reveal Action Bar with [ View PDF ] and [ Download PDF ]
          if (this.pdfSuccessActions) {
            this.pdfSuccessActions.classList.remove('d-none');
            if (this.pdfSuccessFileName) this.pdfSuccessFileName.textContent = filename;
          }

          // Display "<Language> Fitness Report generated successfully."
          if (statusAlert) {
            statusAlert.className = 'alert alert-success py-2 px-3 rounded-3 mb-3 d-flex align-items-center gap-2 shadow-sm';
            if (statusSpinner) statusSpinner.classList.add('d-none');
            if (successIcon) successIcon.classList.remove('d-none');
            if (statusText) statusText.textContent = `${langName} Fitness Report generated successfully.`;
            setTimeout(() => {
              statusAlert.classList.add('d-none');
            }, 5000);
          }
        } catch (err) {
          console.error('PDF Export error:', err);
          if (statusAlert) {
            statusAlert.className = 'alert alert-danger py-2 px-3 rounded-3 mb-3 d-flex align-items-center gap-2 shadow-sm';
            if (statusSpinner) statusSpinner.classList.add('d-none');
            if (successIcon) successIcon.classList.add('d-none');
            if (statusText) statusText.textContent = err.message || 'Error generating report PDF.';
          }
        } finally {
          pdfBtn.disabled = false;
          if (this.previewBtn) this.previewBtn.disabled = false;
          pdfBtn.innerHTML = originalHtml;
        }
      });
    }

    // Wire [ View PDF ] action button
    if (this.viewPdfBtn) {
      this.viewPdfBtn.addEventListener('click', () => {
        if (this.latestPdfBlob) {
          const viewUrl = window.URL.createObjectURL(this.latestPdfBlob);
          window.open(viewUrl, '_blank');
        }
      });
    }

    // Wire [ Download PDF ] action button
    if (this.savePdfBtn) {
      this.savePdfBtn.addEventListener('click', () => {
        if (this.latestPdfBlob) {
          const downloadUrl = window.URL.createObjectURL(this.latestPdfBlob);
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.setAttribute('download', this.latestPdfFilename || `UMS_Fitness_Report_${this.currentArmyNumber}.pdf`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(downloadUrl);
        }
      });
    }
    // Retrain modal trigger
    const retrainBtn = document.getElementById('triggerRetrainBtn');
    if (retrainBtn) {
      retrainBtn.addEventListener('click', () => this.triggerModelRetrain());
    }
  }

  updateTotalCounts(count) {
    const formatted = count !== null && count !== undefined ? count : '--';
    if (this.totalPersonnelCount) this.totalPersonnelCount.textContent = formatted;
    if (this.searchCardTotalCount) this.searchCardTotalCount.textContent = formatted;
    if (this.welcomeTotalCount) this.welcomeTotalCount.textContent = formatted;
  }

  updateActiveSearchItem(items) {
    items.forEach((it, idx) => {
      if (idx === this.activeSearchIndex) {
        it.classList.add('active-item');
        it.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        it.classList.remove('active-item');
      }
    });
  }

  async performSearch(query = '', showDropdown = false) {
    this.latestSearchQuery = query;
    try {
      const res = await fetch(`/fitness/api/personnel-list?q=${encodeURIComponent(query)}&limit=15`);
      const json = await res.json();
      if (this.latestSearchQuery !== query) return;

      if (json.success) {
        if (json.total_count !== undefined) {
          this.updateTotalCounts(json.total_count);
        }
        this.renderSearchResults(json.data, showDropdown, json.total_count);
      }
    } catch (e) {
      console.error("Search error:", e);
    }
  }

  loadInitialSearch() {
    this.performSearch('', false);
    
    // Check URL search parameters or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const targetArmyNo = urlParams.get('army_number') || localStorage.getItem('fitnessTargetArmyNo');
    
    if (targetArmyNo) {
      localStorage.removeItem('fitnessTargetArmyNo');
      this.searchInput.value = targetArmyNo;
      if (this.clearBtn) this.clearBtn.classList.remove('d-none');
      this.loadAnalysis(targetArmyNo, this.currentGoal);
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  highlightMatch(text, query) {
    if (!text) return '';
    const textStr = String(text);
    const currentInputValue = (this.searchInput ? this.searchInput.value : '').trim();
    const effectiveQuery = (query || currentInputValue || '').trim();

    if (!effectiveQuery) return this.escapeHtml(textStr);
    
    const q = effectiveQuery;
    const escapedQuery = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escapedQuery})`, 'gi');
    
    const parts = textStr.split(regex);
    if (parts.length <= 1) return this.escapeHtml(textStr);

    return parts.map(part => {
      if (part.toLowerCase() === q.toLowerCase()) {
        return `<span class="search-highlight">${this.escapeHtml(part)}</span>`;
      }
      return this.escapeHtml(part);
    }).join('');
  }

  getInitials(name) {
    if (!name) return 'SO';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  renderSearchResults(soldiers, showDropdown = true, totalCount = null) {
    this.searchResults.innerHTML = '';
    this.activeSearchIndex = -1;

    const currentQuery = (this.searchInput ? this.searchInput.value : '').trim();

    if (!soldiers || soldiers.length === 0) {
      this.searchResults.innerHTML = `
        <div class="p-3 text-muted text-center small font-monospace">
          <i class="fas fa-search text-warning me-1"></i> No personnel found matching query "${this.escapeHtml(currentQuery)}".
        </div>
      `;
      if (showDropdown && document.activeElement === this.searchInput) {
        this.searchResults.classList.remove('d-none');
      }
      return;
    }

    soldiers.forEach(s => {
      const item = document.createElement('div');
      item.className = 'search-item';
      
      const badgeClass = s.status_type === 'category' ? 'bg-danger' : 'bg-success';
      const statusText = s.status_type === 'category' ? 'LMC' : 'SHAPE-1';
      const initials = this.getInitials(s.name);

      const highlightedName = this.highlightMatch(s.name, currentQuery);
      const highlightedArmyNo = this.highlightMatch(s.army_number, currentQuery);
      const highlightedCompany = this.highlightMatch(s.company || 'Unit HQ', currentQuery);
      const highlightedRank = this.highlightMatch(s.rank || 'Soldier', currentQuery);

      item.innerHTML = `
        <div class="d-flex align-items-center gap-3 flex-grow-1 min-w-0">
          <div class="search-soldier-avatar flex-shrink-0">${initials}</div>
          <div class="flex-grow-1 min-w-0">
            <div class="fw-bold text-truncate" style="color: var(--fit-text-main); font-size: 0.95rem; line-height: 1.3;">
              ${highlightedName} <span class="badge bg-secondary text-white ms-1 fw-semibold" style="font-size: 0.72rem; vertical-align: middle;">${highlightedRank}</span>
            </div>
            <div class="small text-muted d-flex align-items-center flex-wrap gap-2 mt-1" style="font-size: 0.82rem; line-height: 1.4;">
              <span class="search-soldier-army-no">${highlightedArmyNo}</span>
              <span class="text-muted opacity-50">&bull;</span>
              <span class="fw-medium text-secondary">${highlightedCompany}</span>
              <span class="text-muted opacity-50">&bull;</span>
              <span class="fw-medium text-secondary">${s.trade || 'GD'}</span>
            </div>
          </div>
        </div>
        <div class="text-end flex-shrink-0 ms-2">
          <span class="badge ${badgeClass} text-uppercase px-2 py-1 shadow-sm" style="font-size: 0.72rem; letter-spacing: 0.5px;">${statusText}</span>
          <div class="small text-muted fw-bold mt-1" style="font-size: 0.8rem;">${s.weight ? s.weight + ' kg' : 'Wt: --'}</div>
        </div>
      `;

      item.addEventListener('click', (e) => {
        e.stopPropagation();
        this.searchInput.value = `${s.name} (${s.army_number})`;
        if (this.clearBtn) this.clearBtn.classList.remove('d-none');
        this.searchResults.classList.add('d-none');
        this.searchInput.blur();
        this.loadAnalysis(s.army_number, this.currentGoal);
      });

      this.searchResults.appendChild(item);
    });

    if (totalCount !== null && totalCount !== undefined) {
      const footer = document.createElement('div');
      footer.className = 'p-2 px-3 bg-light border-top text-muted small d-flex justify-content-between align-items-center font-monospace';
      footer.style.fontSize = '0.78rem';
      footer.innerHTML = `
        <span><i class="fas fa-list me-1 text-primary"></i> Showing ${soldiers.length}</span>
        <span><i class="fas fa-database me-1 text-primary"></i> Total Weight Info: <strong>${totalCount}</strong></span>
      `;
      this.searchResults.appendChild(footer);
    }

    if (showDropdown && document.activeElement === this.searchInput) {
      this.searchResults.classList.remove('d-none');
    } else {
      this.searchResults.classList.add('d-none');
    }
  }

  async loadAnalysis(armyNumber, goal = 'Overall Fitness') {
    this.currentArmyNumber = armyNumber;
    this.currentGoal = goal;

    this.welcomeState.classList.add('d-none');
    this.activeContent.classList.add('d-none');
    this.errorAlert.classList.add('d-none');
    this.loadingState.classList.remove('d-none');

    try {
      const res = await fetch('/fitness/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          army_number: armyNumber,
          goal: goal,
          lang: this.currentLang || 'en'
        })
      });

      const json = await res.json();
      this.loadingState.classList.add('d-none');

      if (!json.success) {
        if (this.pdfBtn) this.pdfBtn.disabled = true;
        if (this.previewBtn) this.previewBtn.disabled = true;
        this.errorAlert.textContent = json.error || 'Failed to analyze soldier records.';
        this.errorAlert.classList.remove('d-none');
        return;
      }

      this.currentData = json;
      if (this.pdfBtn) this.pdfBtn.disabled = false;
      if (this.previewBtn) this.previewBtn.disabled = false;
      this.renderAllStages(json);
      this.activeContent.classList.remove('d-none');
      this.switchStage(this.activeStage);
    } catch (e) {
      if (this.pdfBtn) this.pdfBtn.disabled = true;
      if (this.previewBtn) this.previewBtn.disabled = true;
      this.loadingState.classList.add('d-none');
      this.errorAlert.textContent = 'Server connection error. Please try again.';
      this.errorAlert.classList.remove('d-none');
      console.error(e);
    }
  }

  switchStage(stageName) {
    if (!this.stageViews[stageName]) return;
    this.activeStage = stageName;

    // Update Tab Buttons
    if (this.stageNav) {
      this.stageNav.querySelectorAll('.workflow-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-stage') === stageName) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    // Toggle Stage Views
    Object.keys(this.stageViews).forEach(key => {
      if (this.stageViews[key]) {
        if (key === stageName) {
          this.stageViews[key].classList.remove('d-none');
        } else {
          this.stageViews[key].classList.add('d-none');
        }
      }
    });

    // Refresh charts when switching to analysis or progression view
    if (stageName === 'analysis') {
      this.renderAnalysisCharts();
    } else if (stageName === 'progression') {
      this.renderProgressionChart();
    }
  }

  renderAllStages(data) {
    this.renderProfileCard(data.soldier);
    this.renderAnalysisCard(data.soldier);
    this.renderPredictionCard(data.soldier, data.prediction, data.recommendations);
    this.renderRecommendationsCard(data.soldier, data.recommendations);
    this.renderProgressionCard(data.progression);
    this.renderReportPreview(data);
  }

  renderProfileCard(s) {
    document.getElementById('profSoldierName').textContent = s.name || 'Unknown';
    document.getElementById('profArmyNumber').textContent = s.army_number || 'N/A';
    document.getElementById('profRank').textContent = s.rank || 'Soldier';
    document.getElementById('profCompany').textContent = s.company || 'Unit HQ';
    document.getElementById('profTrade').textContent = s.trade || 'GD';
    document.getElementById('profSection').textContent = s.section || 'N/A';
    
    document.getElementById('profAge').textContent = s.age ? `${s.age} yrs` : 'N/A';
    document.getElementById('profHeight').textContent = s.height_cm ? `${s.height_cm} cm` : 'N/A';
    document.getElementById('profActualWeight').textContent = s.actual_weight_kg ? `${s.actual_weight_kg} kg` : 'N/A';
    document.getElementById('profIdealWeight').textContent = s.ideal_weight_kg ? `${s.ideal_weight_kg} kg` : 'N/A';
    
    const diffKg = s.weight_difference_kg !== null && s.weight_difference_kg !== undefined
      ? `${s.weight_difference_kg > 0 ? '+' : ''}${s.weight_difference_kg} kg`
      : '';

    const rawStatus = (s.weight_status || 'N/A').trim();
    const baseStatus = rawStatus.replace(/\s*\([+\-\d.]+%\)/g, '').trim();
    let diffPct = '';
    if (s.weight_deviation_percent !== null && s.weight_deviation_percent !== undefined) {
      const pctVal = Number(s.weight_deviation_percent);
      if (!isNaN(pctVal) && Math.abs(pctVal) > 0.05) {
        diffPct = ` (${pctVal > 0 ? '+' : ''}${pctVal.toFixed(1)}%)`;
      }
    }
    const cleanWeightStatus = baseStatus !== 'N/A' ? `${baseStatus}${diffPct}` : 'N/A';

    const profStatusEl = document.getElementById('profWeightStatus');
    if (profStatusEl) profStatusEl.textContent = cleanWeightStatus;

    const profSubEl = document.getElementById('profWeightSub');
    if (profSubEl) {
      profSubEl.textContent = diffKg ? `${diffKg} Variance vs Standard (Authorization Benchmark)` : 'Authorization Benchmark';
    }
    
    // BPET & PPT Badges
    const bpetEl = document.getElementById('profBpetBadge');
    bpetEl.textContent = s.bpet_grade || 'Untested';
    bpetEl.className = `badge ${s.bpet_grade === 'EXCELLENT' ? 'bg-success' : (s.bpet_grade === 'GOOD' ? 'bg-primary' : 'bg-secondary')}`;
    
    const pptEl = document.getElementById('profPptBadge');
    pptEl.textContent = s.ppt_grade || 'Untested';
    pptEl.className = `badge ${s.ppt_grade === 'EXCELLENT' ? 'bg-success' : (s.ppt_grade === 'GOOD' ? 'bg-primary' : 'bg-secondary')}`;
    
    document.getElementById('profSportsList').textContent = s.sports_list || 'None';
    document.getElementById('profPrimarySport').textContent = s.primary_sport || 'None';
    document.getElementById('profSportCount').textContent = s.sport_count || '0';
    
    // Medical & Restrictions
    const medBadge = document.getElementById('profMedBadge');
    if (s.has_medical_restriction || s.is_low_medical_category) {
      medBadge.textContent = 'Restricted / LMC';
      medBadge.className = 'badge bg-danger';
    } else {
      medBadge.textContent = 'SHAPE-1 Cleared';
      medBadge.className = 'badge bg-success';
    }
    
    document.getElementById('profRestrictionsText').textContent = s.restrictions || s.medical_problem || 'None (Medically Cleared)';
    
    // Data quality warning flags
    const flagsCont = document.getElementById('profQualityFlagsContainer');
    if (s.data_quality_flags && s.data_quality_flags.length > 0) {
      flagsCont.innerHTML = s.data_quality_flags.map(f => `<div class="badge bg-warning text-dark me-1 mb-1"><i class="fas fa-exclamation-triangle me-1"></i>${f}</div>`).join('');
      flagsCont.classList.remove('d-none');
    } else {
      flagsCont.classList.add('d-none');
    }
  }

  renderAnalysisCard(s) {
    document.getElementById('anaBmiVal').textContent = s.bmi || 'N/A';
    document.getElementById('anaBmiCat').textContent = s.bmi_category || 'N/A';
    document.getElementById('anaBmiCat').style.color = s.bmi_color || '#3b82f6';
    
    document.getElementById('anaWeightStatus').textContent = cleanWeightStatus;
    
    const diffKg = s.weight_difference_kg !== null && s.weight_difference_kg !== undefined
      ? `${s.weight_difference_kg > 0 ? '+' : ''}${s.weight_difference_kg} kg`
      : '';

    const anaSubEl = document.getElementById('anaWeightSub');
    if (anaSubEl) {
      anaSubEl.textContent = diffKg ? `${diffKg} Variance vs Standard (Authorization Benchmark)` : 'Authorization Benchmark';
    }

    document.getElementById('anaCombinedPhysical').textContent = `${s.ground_truth_score || 70} / 100`;
    document.getElementById('anaActivityLevel').textContent = s.physical_activity_level || 'Moderate';
  }

  renderAnalysisCharts() {
    const s = this.currentData.soldier;
    if (!s) return;

    // 1. Weight Comparison Bar Chart
    const ctxWeight = document.getElementById('chartWeightComp');
    if (ctxWeight) {
      if (this.charts.weightComp) this.charts.weightComp.destroy();
      this.charts.weightComp = new Chart(ctxWeight, {
        type: 'bar',
        data: {
          labels: ['Actual Weight', 'Ideal Reference', 'Authorized Upper Limit (+10%)'],
          datasets: [{
            data: [
              s.actual_weight_kg || 0,
              s.ideal_weight_kg || 0,
              s.ideal_weight_kg ? Math.round(s.ideal_weight_kg * 1.1) : 0
            ],
            backgroundColor: [
              s.weight_difference_kg > 5 ? '#f59e0b' : '#3b82f6',
              '#10b981',
              '#94a3b8'
            ],
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: false, min: Math.max(0, (s.ideal_weight_kg || 60) - 20) } }
        }
      });
    }

    // 2. Physical Readiness Radar Chart
    const ctxRadar = document.getElementById('chartPhysicalRadar');
    if (ctxRadar) {
      if (this.charts.radar) this.charts.radar.destroy();
      this.charts.radar = new Chart(ctxRadar, {
        type: 'radar',
        data: {
          labels: ['BPET Endurance', 'PPT Calisthenics', 'Weight Compliance', 'Sports Activity', 'Medical Clearance'],
          datasets: [{
            label: s.name || 'Soldier Profile',
            data: [
              s.bpet_score || 70,
              s.ppt_score || 70,
              Math.max(20, 100 - (Math.abs(s.weight_deviation_percent || 0) * 3)),
              Math.min(100, (s.sport_count || 0) * 40 + 20),
              s.has_medical_restriction ? 40 : 100
            ],
            backgroundColor: 'rgba(59, 130, 246, 0.25)',
            borderColor: '#3b82f6',
            borderWidth: 2,
            pointBackgroundColor: '#3b82f6'
          }]
        },
        options: {
          responsive: true,
          scales: {
            r: {
              angleLines: { color: 'rgba(150, 150, 150, 0.2)' },
              suggestedMin: 0,
              suggestedMax: 100
            }
          }
        }
      });
    }
  }

  renderPredictionCard(s, pred, rec) {
    const scoreVal = pred.fitness_score || 70;
    document.getElementById('predScoreNumber').textContent = scoreVal;
    
    const circle = document.getElementById('predScoreCircle');
    if (circle) {
      circle.style.setProperty('--score-val', scoreVal);
      circle.style.setProperty('--score-color', pred.category_color || '#10b981');
    }
    
    const catBadge = document.getElementById('predCategoryBadge');
    catBadge.textContent = pred.category_label || pred.fitness_category;
    catBadge.style.backgroundColor = pred.category_color || '#10b981';
    
    document.getElementById('predConfidenceVal').textContent = `${pred.confidence_score}%`;
    document.getElementById('predConfidenceBar').style.width = `${pred.confidence_score}%`;
    document.getElementById('predModelVer').textContent = pred.model_version || 'v1';
    document.getElementById('predAlgorithm').textContent = pred.algorithm || 'GradientBoostingClassifier';
    
    // Strengths
    let rawStrengths = (pred.strengths && Array.isArray(pred.strengths) && pred.strengths.length > 0)
      ? pred.strengths
      : ((pred.key_strengths && Array.isArray(pred.key_strengths) && pred.key_strengths.length > 0) ? pred.key_strengths : []);
    let strengthsList = [...rawStrengths];
    if (strengthsList.length === 0) {
      strengthsList = [
        'Medical SHAPE-1 Clearance: Fully cleared for unrestricted physical training with zero contraindications.',
        'Active Demographic Resilience: Operational baseline age and active service profile support progressive conditioning.',
        'Metabolic Adaptability: Strong physiological responsiveness to structured military nutrition and targeted caloric balance.',
        'Cardiovascular Conditioning: Baseline aerobic capacity capable of sustaining progressive 5km road-run tempos.'
      ];
    }

    const strengthsCont = document.getElementById('predStrengthsList');
    if (strengthsCont) {
      strengthsCont.innerHTML = strengthsList.map(str => `
        <li class="factor-item strength">
          <i class="fas fa-check-circle factor-icon text-success"></i>
          <span>${str}</span>
        </li>
      `).join('');
    }
    
    // Improvements
    let rawImprovements = (pred.improvements && Array.isArray(pred.improvements) && pred.improvements.length > 0)
      ? pred.improvements
      : ((pred.risk_factors && Array.isArray(pred.risk_factors) && pred.risk_factors.length > 0) ? pred.risk_factors : []);
    let improvementsList = [...rawImprovements];
    if (improvementsList.length === 0) {
      improvementsList = [
        'Threshold Aerobic Stamina: Sustain high-intensity interval training (HIIT) to maintain peak cardiovascular VO2 max.',
        'Tactical Load Carriage: Progressively incorporate weighted endurance marches (BPET battle-load conditioning).',
        'Core & Lumbar Spine Stability: Integrate functional abdominal, glute bridge, and spinal stability drills.',
        'Hydration Discipline: Maintain strict 3.5+ L daily hydration during demanding field activities.'
      ];
    }

    const improveCont = document.getElementById('predImprovementsList');
    if (improveCont) {
      improveCont.innerHTML = improvementsList.map(imp => `
        <li class="factor-item improvement">
          <i class="fas fa-arrow-circle-up factor-icon text-warning"></i>
          <span>${imp}</span>
        </li>
      `).join('');
    }

    // Targeted Nutritional Metrics in Prediction Results View
    if (rec && rec.diet) {
      const diet = rec.diet;
      const targetCalsEl = document.getElementById('predTargetCals');
      if (targetCalsEl) targetCalsEl.textContent = `${diet.target_calories} kcal / Day`;

      const carbEl = document.getElementById('predCarbGrams');
      if (carbEl && diet.macros) carbEl.textContent = `${diet.macros.carb_grams}g (${diet.macros.carb_pct}%)`;

      const fatEl = document.getElementById('predFatGrams');
      if (fatEl && diet.macros) fatEl.textContent = `${diet.macros.fat_grams}g (${diet.macros.fat_pct}%)`;

      const proteinEl = document.getElementById('predProteinGrams');
      if (proteinEl && diet.macros) proteinEl.textContent = `${diet.macros.protein_grams}g (${diet.macros.protein_pct}%)`;

      const hydEl = document.getElementById('predHydration');
      if (hydEl) hydEl.textContent = `${diet.hydration_liters} L / Day`;
    }
  }

  renderRecommendationsCard(s, rec) {
    // Medical Notice
    const medNotice = rec.medical_notice;
    const alertBox = document.getElementById('recMedicalAlert');
    if (alertBox) {
      alertBox.className = `alert alert-${medNotice.alert_class || 'info'} d-flex align-items-center mb-4`;
      alertBox.innerHTML = `
        <i class="fas ${medNotice.is_restricted ? 'fa-exclamation-triangle' : 'fa-shield-alt'} fa-2x me-3"></i>
        <div>
          <h6 class="fw-bold mb-1">${medNotice.title}</h6>
          <p class="mb-0 small">${medNotice.message}</p>
        </div>
      `;
    }

    // Diet
    const diet = rec.diet;
    document.getElementById('recTargetCals').textContent = `${diet.target_calories} kcal`;
    document.getElementById('recDietStrategy').textContent = diet.strategy;
    document.getElementById('recProteinGrams').textContent = `${diet.macros.protein_grams}g (${diet.macros.protein_pct}%)`;
    document.getElementById('recCarbGrams').textContent = `${diet.macros.carb_grams}g (${diet.macros.carb_pct}%)`;
    document.getElementById('recFatGrams').textContent = `${diet.macros.fat_grams}g (${diet.macros.fat_pct}%)`;
    document.getElementById('recHydration').textContent = `${diet.hydration_liters} Liters / Day`;
    
    // Meal Schedule Table
    const menuTbody = document.getElementById('recMenuTableBody');
    if (menuTbody && diet.sample_menu) {
      menuTbody.innerHTML = diet.sample_menu.map(m => `
        <tr>
          <td class="fw-bold text-nowrap text-primary" style="width: 25%;">${m.meal}</td>
          <td>${m.items}</td>
        </tr>
      `).join('');
    }

    // Exercise Plan
    const ex = rec.exercise;
    document.getElementById('recExerciseTitle').textContent = ex.title;
    document.getElementById('recExerciseFocus').textContent = ex.focus_area;
    
    const exTbody = document.getElementById('recExerciseTableBody');
    if (exTbody && ex.exercises) {
      exTbody.innerHTML = ex.exercises.map(item => `
        <tr>
          <td class="fw-bold">${item.exercise}</td>
          <td>${item.sets}</td>
          <td>${item.reps}</td>
          <td>${item.duration}</td>
          <td>${item.frequency}</td>
          <td><span class="badge ${item.intensity === 'High' ? 'bg-danger' : (item.intensity === 'Moderate' ? 'bg-primary' : 'bg-info')}">${item.intensity}</span></td>
        </tr>
      `).join('');
    }

    // Blocked exercises if any
    const blockedCont = document.getElementById('recBlockedExercisesCont');
    if (ex.blocked_exercises && ex.blocked_exercises.length > 0) {
      blockedCont.innerHTML = `
        <div class="alert alert-warning mt-3 mb-0">
          <h6 class="fw-bold"><i class="fas fa-ban me-1"></i> Contraindicated Exercises Blocked by Safety Engine:</h6>
          <ul class="mb-0 small ps-3">
            ${ex.blocked_exercises.map(b => `<li><strong>${b.exercise}:</strong> ${b.reason}</li>`).join('')}
          </ul>
        </div>
      `;
      blockedCont.classList.remove('d-none');
    } else {
      blockedCont.classList.add('d-none');
    }
  }

  renderProgressionCard(prog) {
    const miles = prog.milestones || [];
    const cont = document.getElementById('progMilestonesContainer');
    if (cont) {
      cont.innerHTML = miles.map(m => `
        <div class="col-md-3 mb-3">
          <div class="milestone-card h-100">
            <div class="fw-bold text-primary mb-2">${m.period}</div>
            <div class="d-flex justify-content-between mb-1 small">
              <span class="text-muted">Target Weight:</span>
              <span class="fw-bold">${m.weight_kg} kg</span>
            </div>
            <div class="d-flex justify-content-between mb-1 small">
              <span class="text-muted">Projected BMI:</span>
              <span class="fw-bold">${m.bmi}</span>
            </div>
            <div class="d-flex justify-content-between mb-2 small">
              <span class="text-muted">Readiness Score:</span>
              <span class="fw-bold text-success">${m.fitness_score} / 100</span>
            </div>
            <hr class="my-2" style="opacity: 0.15;">
            <div class="small text-muted mb-1"><strong>Endurance:</strong> ${m.bpet_target}</div>
            <div class="small text-muted"><strong>Calisthenics:</strong> ${m.ppt_target}</div>
          </div>
        </div>
      `).join('');
    }
  }

  renderProgressionChart() {
    const prog = this.currentData.progression;
    if (!prog || !prog.chart_data) return;

    const ctx = document.getElementById('chartProgressionTrajectory');
    if (ctx) {
      if (this.charts.progression) this.charts.progression.destroy();
      this.charts.progression = new Chart(ctx, {
        type: 'line',
        data: {
          labels: prog.chart_data.labels || ['Current Baseline', '30 Days Projected', '60 Days Projected', '90 Days Projected'],
          datasets: [
            {
              label: 'Readiness Score (Actual vs AI Projected)',
              data: prog.chart_data.score_series,
              borderColor: '#059669',
              backgroundColor: 'rgba(5, 150, 105, 0.12)',
              pointBackgroundColor: '#059669',
              pointBorderColor: '#047857',
              pointRadius: 5,
              pointHoverRadius: 7,
              fill: true,
              tension: 0.25,
              yAxisID: 'yScore'
            },
            {
              label: 'Body Weight (Actual vs AI Target kg)',
              data: prog.chart_data.weight_series,
              borderColor: '#2563eb',
              backgroundColor: 'transparent',
              pointBackgroundColor: '#2563eb',
              pointBorderColor: '#1d4ed8',
              pointStyle: 'rectRot',
              pointRadius: 6,
              pointHoverRadius: 8,
              borderDash: [5, 4],
              fill: false,
              tension: 0.25,
              yAxisID: 'yWeight'
            }
          ]
        },
        options: {
          responsive: true,
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: {
              position: 'top',
              labels: {
                boxWidth: 14,
                font: { weight: 'bold', size: 12 }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.dataset.label || '';
                  const val = context.parsed.y;
                  if (context.datasetIndex === 0) {
                    return `${label}: ${val} / 100 PTS`;
                  }
                  return `${label}: ${val} kg`;
                }
              }
            }
          },
          scales: {
            yScore: {
              type: 'linear',
              position: 'left',
              min: 40,
              max: 100,
              title: { display: true, text: 'Readiness Score (PTS)', color: '#059669', font: { weight: 'bold' } },
              ticks: { color: '#059669' }
            },
            yWeight: {
              type: 'linear',
              position: 'right',
              grid: { drawOnChartArea: false },
              title: { display: true, text: 'Body Weight (kg)', color: '#2563eb', font: { weight: 'bold' } },
              ticks: { color: '#2563eb' }
            }
          }
        }
      });
    }
  }

  renderReportPreview(data) {
    const previewCont = document.getElementById('reportHtmlPreviewCont');
    if (!previewCont) return;

    const s = data.soldier || {};
    const pred = data.prediction || {};
    const rec = data.recommendations || {};
    const prog = data.progression || {};
    const lbl = data.labels || {};
    const lang = this.currentLang || data.lang || 'en';
    const isRtl = lang === 'ur';

    // Helper to get translated label with fallback
    const t = (key, fallback) => (lbl && lbl[key]) ? lbl[key] : fallback;

    // Update Stage 6 Preview Card title & button text if available
    const prevTitleEl = document.getElementById('reportPreviewTitle');
    if (prevTitleEl) prevTitleEl.textContent = t('official_preview_title', 'Official Individual Fitness Report Preview');
    const prevBtnTextEl = document.getElementById('reportPreviewDownloadText');
    if (prevBtnTextEl) prevBtnTextEl.textContent = t('download_pdf', 'Download PDF Document');

    previewCont.innerHTML = `
      <div class="card p-4 shadow-sm border" style="background: white; color: #1e293b; max-width: 900px; margin: 0 auto; font-family: 'Segoe UI', Arial, sans-serif; ${isRtl ? 'direction: rtl; text-align: right;' : ''}">
        <!-- Official Regiment Header Banner -->
        <div class="page-title mb-4" style="height: auto; min-height: 95px; background: linear-gradient(135deg, #3c425c 0%, #764ba2 100%) !important; color: white; padding: 0.8rem 1.4rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25); display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
          <img src="/static/image_for_login_page/rt.jpg" class="org-logo" alt="Unit Logo" style="width: 75px; height: 75px; object-fit: contain; border-radius: 20%; padding: 6px; background: rgba(255, 255, 255, 0.15); flex-shrink: 0;">
          <div class="title-section text-center flex-grow-1">
            <h4 class="fw-bold mb-1 text-white" style="font-size: 1.35rem; letter-spacing: 0.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">${t('unit_title', 'UNIT MANAGEMENT SYSTEM')}</h4>
            <div style="display: inline-block; background: rgba(15, 23, 42, 0.45); border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 999px; padding: 3px 14px; font-size: 0.8rem; font-weight: 600; color: rgba(255, 255, 255, 0.95); margin-top: 3px;">
              ${t('report_title', 'Personal Fitness Report')}
            </div>
            <div class="small text-white-50 mt-1" style="font-size: 0.72rem;">${t('military_record_sub', 'UNIT MANAGEMENT SYSTEM • OFFICIAL MILITARY RECORD • CONFIDENTIAL')} &bull; ${t('report_generated', 'Generated')}: ${new Date().toLocaleDateString(lang === 'hi' ? 'hi-IN' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })} hrs</div>
          </div>
          <img src="/static/image_for_login_page/chinar.jpg" class="org-logo" alt="15 COR Logo" style="width: 75px; height: 75px; object-fit: contain; border-radius: 20%; padding: 6px; background: rgba(255, 255, 255, 0.15); flex-shrink: 0;">
        </div>

        <table class="table table-bordered table-sm mb-3" style="font-size: 0.88rem;">
          <tr style="background: #f1f5f9;">
            <th style="width: 20%;">${t('name', 'Name')}</th><td>${s.name || 'N/A'}</td>
            <th style="width: 20%;">${t('army_number', 'Army Number')}</th><td>${s.army_number || 'N/A'}</td>
          </tr>
          <tr>
            <th>${t('rank_trade', 'Rank / Trade')}</th><td>${s.rank || 'N/A'} / ${s.trade || 'N/A'}</td>
            <th>${t('company_section', 'Company / Section')}</th><td>${s.company || 'N/A'} / ${s.section || 'N/A'}</td>
          </tr>
          <tr style="background: #f1f5f9;">
            <th>${t('height_weight', 'Height / Weight')}</th><td>${s.height_cm} cm / ${s.actual_weight_kg} kg</td>
            <th>${t('ideal_wt_dev', 'Ideal Wt / Deviation')}</th><td>${s.ideal_weight_kg || 'N/A'} kg (${s.weight_deviation_percent > 0 ? '+' : ''}${s.weight_deviation_percent}%)</td>
          </tr>
          <tr>
            <th>${t('bmi_cat', 'BMI & Category')}</th><td>${s.bmi || 'N/A'} (${s.bmi_category || 'N/A'})</td>
            <th>${t('bpet_ppt_grading', 'BPET / PPT Grading')}</th><td>${s.bpet_grade || 'N/A'} / ${s.ppt_grade || 'N/A'}</td>
          </tr>
        </table>

        <div class="p-3 mb-3 rounded" style="background: rgba(59, 130, 246, 0.08); border-left: 5px solid #3b82f6;">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <div class="small text-muted text-uppercase fw-bold">${t('readiness_prediction', 'AI Physical Readiness Prediction')}</div>
              <h3 class="fw-bold mb-0 text-primary">${pred.fitness_score} / 100 &mdash; ${pred.category_label || pred.fitness_category}</h3>
            </div>
            <div class="text-end">
              <span class="badge bg-primary fs-6">${t('confidence', 'Confidence')}: ${pred.confidence_score}%</span>
            </div>
          </div>
        </div>

        <div class="row mb-3">
          <div class="col-6">
            <h6 class="fw-bold text-success mb-2"><i class="fas fa-check-circle me-1"></i> ${t('key_positive_factors', 'Key Positive Factors:')}</h6>
            <ul class="small ps-3 mb-0">${(pred.strengths || []).map(str => `<li>${str}</li>`).join('')}</ul>
          </div>
          <div class="col-6">
            <h6 class="fw-bold text-warning mb-2"><i class="fas fa-arrow-circle-up me-1"></i> ${t('action_areas', 'Priority Action Areas:')}</h6>
            <ul class="small ps-3 mb-0">${(pred.improvements || []).map(imp => `<li>${imp}</li>`).join('')}</ul>
          </div>
        </div>

        <hr class="my-3">
        <h6 class="fw-bold text-primary mb-2"><i class="fas fa-utensils me-1"></i> ${t('sec4_title', '4. Personalized Dietary & Macronutrient Plan')} (${rec.diet ? rec.diet.target_calories : 0} kcal / Day):</h6>
        <div class="row g-2 mb-2 text-center">
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">${t('complex_carbs', 'COMPLEX CARBS')}</small>
              <strong class="text-success" style="color: #10b981 !important; font-size: 0.95rem;">${rec.diet && rec.diet.macros ? rec.diet.macros.carb_grams : 0}g (${rec.diet && rec.diet.macros ? rec.diet.macros.carb_pct : 0}%)</strong>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">${t('healthy_fats', 'HEALTHY FATS')}</small>
              <strong class="text-warning" style="color: #f59e0b !important; font-size: 0.95rem;">${rec.diet && rec.diet.macros ? rec.diet.macros.fat_grams : 0}g (${rec.diet && rec.diet.macros ? rec.diet.macros.fat_pct : 0}%)</strong>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">${t('daily_protein', 'DAILY PROTEIN')}</small>
              <strong class="text-primary" style="color: #3b82f6 !important; font-size: 0.95rem;">${rec.diet && rec.diet.macros ? rec.diet.macros.protein_grams : 0}g (${rec.diet && rec.diet.macros ? rec.diet.macros.protein_pct : 0}%)</strong>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">${t('hydration', 'HYDRATION')}</small>
              <strong class="text-info" style="color: #06b6d4 !important; font-size: 0.95rem;">${rec.diet ? rec.diet.hydration_liters : 0} L / Day</strong>
            </div>
          </div>
        </div>
        <p class="small text-muted mb-3">${rec.diet ? rec.diet.strategy : ''}</p>

        <h6 class="fw-bold text-primary mb-2 mt-2"><i class="fas fa-running me-1"></i> ${t('sec5_title', '5. Physical Training')}:</h6>
        <p class="small text-muted mb-2">${rec.exercise ? rec.exercise.title : ''} &mdash; ${rec.exercise ? rec.exercise.focus_area : ''}</p>
      </div>
    `;
  }

  async triggerModelRetrain() {
    const statusCont = document.getElementById('retrainStatusMsg');
    statusCont.innerHTML = `<div class="text-primary"><div class="spinner-border spinner-border-sm me-2"></div>Retraining fitness models on active database records...</div>`;
    
    try {
      const res = await fetch('/fitness/api/retrain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version: 'v1' })
      });
      const json = await res.json();
      if (json.success) {
        statusCont.innerHTML = `<div class="alert alert-success mb-0 py-2"><i class="fas fa-check-circle me-1"></i> Retraining successful! Classifier: ${json.classifier} (Acc: ${json.classifier_accuracy}), Regressor: ${json.regressor} (MAE: ${json.regressor_mae}).</div>`;
      } else {
        statusCont.innerHTML = `<div class="alert alert-danger mb-0 py-2"><i class="fas fa-times-circle me-1"></i> ${json.error || 'Retraining failed.'}</div>`;
      }
    } catch (e) {
      statusCont.innerHTML = `<div class="alert alert-danger mb-0 py-2"><i class="fas fa-times-circle me-1"></i> Server error during retraining.</div>`;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.fitnessApp = new FitnessTrendApp();
});
