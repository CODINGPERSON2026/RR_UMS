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

    // Calculate All Individuals Fitness button handler -> Shows Confirmation Screen
    const btnCalcAll = document.getElementById('btnCalculateAllFitness');
    if (btnCalcAll) {
      btnCalcAll.addEventListener('click', () => {
        this.openCalculateAllConfirmation();
      });
    }

    // Confirm & Calculate All proceed button handler
    const btnConfirmProceed = document.getElementById('btnConfirmProceedCalcAll');
    if (btnConfirmProceed) {
      btnConfirmProceed.addEventListener('click', () => {
        this.executeCalculateAllFitness();
      });
    }

    // Modal Cancel button handler
    const btnCancelCalc = document.getElementById('btnCancelCalcAll');
    if (btnCancelCalc) {
      btnCancelCalc.addEventListener('click', (e) => {
        if (this.isCalculating) {
          e.preventDefault();
          e.stopPropagation();
          this.abortCalculateAllFitness();
        } else {
          const calcModalEl = document.getElementById('calculateAllFitnessModal');
          if (calcModalEl) {
            const bsModal = bootstrap.Modal.getInstance(calcModalEl);
            if (bsModal) bsModal.hide();
          }
        }
      });
    }

    // Modal top-right close button (X) handler
    const closeCalcModalBtn = document.getElementById('closeCalcAllModalBtn');
    if (closeCalcModalBtn) {
      closeCalcModalBtn.addEventListener('click', (e) => {
        if (this.isCalculating) {
          e.preventDefault();
          e.stopPropagation();
          this.abortCalculateAllFitness();
        }
      });
    }
  }

  setCalcModalState(state) {
    const views = {
      confirm: document.getElementById('calcAllConfirmState'),
      loading: document.getElementById('calcAllLoadingState'),
      aborted: document.getElementById('calcAllAbortedState'),
      success: document.getElementById('calcAllSuccessState'),
      error: document.getElementById('calcAllErrorState')
    };

    Object.keys(views).forEach(key => {
      const el = views[key];
      if (el) {
        if (key === state) {
          el.classList.remove('d-none');
          el.style.display = '';
        } else {
          el.classList.add('d-none');
          el.style.display = 'none';
        }
      }
    });

    const modalTitle = document.getElementById('calculateAllFitnessModalLabel');
    const btnConfirm = document.getElementById('btnConfirmProceedCalcAll');
    const btnCancel = document.getElementById('btnCancelCalcAll');

    if (state === 'confirm') {
      if (modalTitle) modalTitle.textContent = 'Unit-Wide AI Fitness Assessment';
      if (btnConfirm) {
        btnConfirm.classList.remove('d-none');
        btnConfirm.style.display = '';
        btnConfirm.disabled = false;
        btnConfirm.innerHTML = '<i class="fas fa-check"></i><span>Confirm &amp; Calculate All</span>';
      }
      if (btnCancel) {
        btnCancel.className = 'btn btn-secondary btn-sm px-4 fw-semibold rounded-pill';
        btnCancel.innerHTML = 'Cancel';
        btnCancel.disabled = false;
      }
    } else if (state === 'loading') {
      if (modalTitle) modalTitle.textContent = 'Unit-Wide AI Fitness Assessment';
      if (btnConfirm) {
        btnConfirm.classList.add('d-none');
        btnConfirm.style.display = 'none';
      }
      if (btnCancel) {
        btnCancel.className = 'btn btn-secondary btn-sm px-4 fw-semibold rounded-pill';
        btnCancel.innerHTML = 'Cancel';
        btnCancel.disabled = false;
      }
    } else if (state === 'aborted') {
      if (modalTitle) modalTitle.textContent = 'Calculation Safely Aborted';
      if (btnConfirm) {
        btnConfirm.classList.add('d-none');
        btnConfirm.style.display = 'none';
      }
      if (btnCancel) {
        btnCancel.className = 'btn btn-secondary btn-sm px-4 fw-semibold rounded-pill';
        btnCancel.innerHTML = 'Close';
        btnCancel.disabled = false;
      }
    } else if (state === 'success') {
      if (modalTitle) modalTitle.textContent = 'Batch Evaluation Completed & Saved';
      if (btnConfirm) {
        btnConfirm.classList.add('d-none');
        btnConfirm.style.display = 'none';
      }
      if (btnCancel) {
        btnCancel.className = 'btn btn-primary btn-sm px-4 fw-bold rounded-pill';
        btnCancel.innerHTML = 'Close';
        btnCancel.disabled = false;
      }
    } else if (state === 'error') {
      if (modalTitle) modalTitle.textContent = 'Calculation Error';
      if (btnConfirm) {
        btnConfirm.classList.remove('d-none');
        btnConfirm.style.display = '';
        btnConfirm.disabled = false;
        btnConfirm.innerHTML = '<i class="fas fa-redo me-1"></i><span>Try Again</span>';
      }
      if (btnCancel) {
        btnCancel.className = 'btn btn-secondary btn-sm px-4 fw-semibold rounded-pill';
        btnCancel.innerHTML = 'Close';
        btnCancel.disabled = false;
      }
    }
  }

  openCalculateAllConfirmation() {
    const modalEl = document.getElementById('calculateAllFitnessModal');
    if (!modalEl) return;

    this.isCalculating = false;
    this.calcAbortController = null;
    this.currentCalcTaskId = null;

    this.setCalcModalState('confirm');

    // Update dynamic personnel count in confirmation message if available
    const confirmCountEl = document.getElementById('calcConfirmPersonnelCount');
    const totalCountText = document.getElementById('totalPersonnelCount')?.textContent?.trim();
    if (confirmCountEl && totalCountText && totalCountText !== '--') {
      confirmCountEl.textContent = totalCountText;
    }

    const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    bsModal.show();
  }

  async abortCalculateAllFitness() {
    this.isAborted = true;
    this.isCalculating = false;

    if (this._calcStatusTimer) {
      clearInterval(this._calcStatusTimer);
      this._calcStatusTimer = null;
    }

    // 1. Immediately switch UI to aborted view
    this.setCalcModalState('aborted');

    // 2. Abort ongoing client-side fetch request
    if (this.calcAbortController) {
      try {
        this.calcAbortController.abort();
      } catch (e) {
        console.warn('AbortController abort warning:', e);
      }
    }

    // 3. Dispatch abort signal to backend to cancel transaction and prevent persistence
    const taskIdToAbort = this.currentCalcTaskId;
    try {
      fetch('/fitness/api/calculate-all/abort', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskIdToAbort || '' }),
        keepalive: true
      }).catch(() => {});
    } catch (e) {}

    try {
      fetch('/api/fitness/calculate-all/abort', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskIdToAbort || '' }),
        keepalive: true
      }).catch(() => {});
    } catch (e) {}
  }

  async executeCalculateAllFitness() {
    if (this.isCalculating) {
      console.warn("Calculation already in progress. Ignoring duplicate trigger.");
      return;
    }

    this.isCalculating = true;
    this.isAborted = false;
    this.calcAbortController = new AbortController();
    this.currentCalcTaskId = 'calc_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8);

    const btnConfirm = document.getElementById('btnConfirmProceedCalcAll');
    if (btnConfirm) btnConfirm.disabled = true;

    this.setCalcModalState('loading');

    const statusMsgs = [
      "Cross-referencing BPET 5km speed & endurance standards...",
      "Evaluating PPT calisthenics, functional pushups & sit-ups...",
      "Computing Body Mass Index (BMI) & Indian Army SHAPE-1 status...",
      "Running multi-model ML predictions across regiment roster...",
      "Filtering results & synchronizing with Command Oversight table..."
    ];
    let msgIdx = 0;
    const statusTextEl = document.getElementById('calcAllStatusText');
    if (statusTextEl) statusTextEl.textContent = statusMsgs[0];
    
    if (this._calcStatusTimer) clearInterval(this._calcStatusTimer);
    this._calcStatusTimer = setInterval(() => {
      msgIdx = (msgIdx + 1) % statusMsgs.length;
      if (statusTextEl && this.isCalculating) {
        statusTextEl.textContent = statusMsgs[msgIdx];
      }
    }, 1300);

    try {
      const res = await fetch('/fitness/api/calculate-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: this.calcAbortController.signal,
        body: JSON.stringify({
          goal: this.currentGoal || 'Overall Fitness',
          lang: this.currentLang || 'en',
          task_id: this.currentCalcTaskId
        })
      });

      if (this._calcStatusTimer) {
        clearInterval(this._calcStatusTimer);
        this._calcStatusTimer = null;
      }

      // Defensive check: only trigger abort if explicitly aborted by user
      if (this.isAborted) {
        console.log("Calculation was aborted by user.");
        this.isCalculating = false;
        this.setCalcModalState('aborted');
        return;
      }

      const data = await res.json();

      if (this.isAborted || data.aborted) {
        console.log("Calculation aborted signal detected.");
        this.isCalculating = false;
        this.setCalcModalState('aborted');
        return;
      }

      if (!data.success) {
        throw new Error(data.error || 'Failed to calculate fitness for all personnel.');
      }

      const totalCountEl = document.getElementById('calcAllTotalCount');
      const unfitCountEl = document.getElementById('calcAllUnfitCount');
      const fitCountEl = document.getElementById('calcAllFitCount');
      const successMsgEl = document.getElementById('calcAllSuccessMessage');

      if (totalCountEl) totalCountEl.textContent = data.total_processed || 0;
      if (unfitCountEl) unfitCountEl.textContent = data.unfit_count || 0;
      if (fitCountEl) fitCountEl.textContent = data.fit_count || 0;
      if (successMsgEl) {
        successMsgEl.textContent = `Successfully evaluated ${data.total_processed} regiment personnel and updated ums.ai_fitness_reports table.`;
      }

      this.isCalculating = false;
      this.setCalcModalState('success');

      // Update dashboard counts and modal table safely in isolated block
      try {
        const dashTotal = document.getElementById('dash-fit-total');
        if (dashTotal) dashTotal.textContent = data.unfit_count || 0;
        const coTotal = document.getElementById('co-fit-total');
        if (coTotal) coTotal.textContent = data.unfit_count || 0;

        if (window.FitnessModalController && typeof window.FitnessModalController.loadModalData === 'function') {
          if (typeof window.FitnessModalController.loadModalStats === 'function') {
            window.FitnessModalController.loadModalStats();
          }
          window.FitnessModalController.loadModalData();
        }
      } catch (uiSyncErr) {
        console.warn('Post-calculation UI sync warning (non-fatal):', uiSyncErr);
      }

    } catch (err) {
      if (this.isAborted || err.name === 'AbortError') {
        this.isCalculating = false;
        this.setCalcModalState('aborted');
        return;
      }

      console.error('Calculate all fitness error:', err);
      this.isCalculating = false;
      this.setCalcModalState('error');

      const errMsgEl = document.getElementById('calcAllErrorMessage');
      if (errMsgEl) errMsgEl.textContent = err.message || 'Error occurred while calculating fitness.';
    } finally {
      this.isCalculating = false;
      if (this._calcStatusTimer) {
        clearInterval(this._calcStatusTimer);
        this._calcStatusTimer = null;
      }
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
    const anaStatusEl = document.getElementById('anaWeightStatus');
    if (anaStatusEl) anaStatusEl.textContent = cleanWeightStatus;
    
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
    try {
      const diet = rec.diet || {};
      this.currentDiet = diet;
      const targetCalsEl = document.getElementById('recTargetCals');
      if (targetCalsEl) targetCalsEl.textContent = `${diet.target_calories || 2400} kcal`;
      const strategyEl = document.getElementById('recDietStrategy');
      if (strategyEl) strategyEl.textContent = diet.strategy || 'Balanced military nutrition plan.';
      const macros = diet.macros || {};
      const protEl = document.getElementById('recProteinGrams');
      if (protEl) protEl.textContent = `${macros.protein_grams || 110}g (${macros.protein_pct || 20}%)`;
      const carbEl = document.getElementById('recCarbGrams');
      if (carbEl) carbEl.textContent = `${macros.carb_grams || 320}g (${macros.carb_pct || 55}%)`;
      const fatEl = document.getElementById('recFatGrams');
      if (fatEl) fatEl.textContent = `${macros.fat_grams || 65}g (${macros.fat_pct || 25}%)`;
      const hydEl = document.getElementById('recHydration');
      if (hydEl) hydEl.textContent = `${diet.hydration_liters || 3.5} Liters / Day`;

      // Mess Category Badge
      const messBadge = document.getElementById('recMessBadge');
      if (messBadge) {
        const messCat = diet.mess_category || 'OR MESS';
        messBadge.textContent = messCat;
        messBadge.className = `badge ${messCat === 'JCO MESS' ? 'bg-warning text-dark' : 'bg-success'} px-3 py-1.5`;
      }

      // Default to Full Week Plan
      this.switchMessDay('full');

      // Render 30-Day Tactical Nutrition Roadmap
      const roadmapGrid = document.getElementById('recRoadmapGrid');
      if (roadmapGrid && Array.isArray(diet.roadmap_30d)) {
        roadmapGrid.innerHTML = diet.roadmap_30d.map(w => `
          <div class="col-md-6 col-lg-3">
            <div class="p-2.5 border rounded bg-white h-100 shadow-sm" style="font-size: 0.8rem;">
              <div class="fw-bold text-primary mb-1">${this.escapeHtml(w.week)}: ${this.escapeHtml(w.phase)}</div>
              <div class="small text-dark mb-1"><strong>Focus:</strong> ${this.escapeHtml(w.focus)}</div>
              <div class="small text-success mb-1"><strong>Strategy:</strong> ${this.escapeHtml(w.mess_strategy || '')}</div>
              <div class="small text-muted"><strong>Target:</strong> ${this.escapeHtml(w.milestone || '')}</div>
            </div>
          </div>
        `).join('');
      }

      // Optional Supplementary Diet Plan
      const optDietCont = document.getElementById('recOptionalDietCont');
      const optDietBody = document.getElementById('recOptionalDietBody');
      if (optDietCont && optDietBody) {
        if (Array.isArray(diet.optional_diet_plan) && diet.optional_diet_plan.length > 0) {
          optDietBody.innerHTML = diet.optional_diet_plan.map(it => `
            <tr>
              <td class="fw-bold text-nowrap text-secondary" style="width: 25%;">${this.escapeHtml(it.item || '')}</td>
              <td class="text-dark">${this.escapeHtml(it.recommendation || '')}</td>
            </tr>
          `).join('');
          optDietCont.classList.remove('d-none');
        } else {
          optDietCont.classList.add('d-none');
        }
      }
    } catch (dietErr) {
      console.error('Error rendering diet card section:', dietErr);
    }

    // Exercise Plan
    try {
      const ex = rec.exercise || rec.workout || {};
      const exTitleEl = document.getElementById('recExerciseTitle');
      if (exTitleEl) exTitleEl.textContent = ex.title || 'Structured Tactical Physical Training Regimen';
      const exFocusEl = document.getElementById('recExerciseFocus');
      if (exFocusEl) exFocusEl.textContent = ex.focus_area || 'Cardiovascular endurance, core stamina, and tactical mobility.';
      
      const exTbody = document.getElementById('recExerciseTableBody');
      if (exTbody && Array.isArray(ex.exercises)) {
        exTbody.innerHTML = ex.exercises.map(item => `
          <tr>
            <td class="fw-bold">
              ${this.escapeHtml(item.exercise || '')}
              ${item.progression_note ? `<div class="small text-muted fst-italic mt-0.5"><i class="fas fa-level-up-alt text-primary me-1"></i>${this.escapeHtml(item.progression_note)}</div>` : ''}
            </td>
            <td>${this.escapeHtml(String(item.sets || '--'))}</td>
            <td>${this.escapeHtml(String(item.reps || '--'))}</td>
            <td>${this.escapeHtml(String(item.duration || '--'))}</td>
            <td>${this.escapeHtml(String(item.frequency || '--'))}</td>
            <td><span class="badge ${item.intensity === 'High' ? 'bg-danger' : (item.intensity === 'Moderate' ? 'bg-primary' : 'bg-info')}">${this.escapeHtml(item.intensity || 'Moderate')}</span></td>
          </tr>
        `).join('');
      }

      // Blocked exercises if any
      const blockedCont = document.getElementById('recBlockedExercisesCont');
      if (blockedCont) {
        if (Array.isArray(ex.blocked_exercises) && ex.blocked_exercises.length > 0) {
          blockedCont.innerHTML = `
            <div class="alert alert-warning mt-3 mb-0">
              <h6 class="fw-bold"><i class="fas fa-ban me-1"></i> Contraindicated Exercises Blocked by Safety Engine:</h6>
              <ul class="mb-0 small ps-3">
                ${ex.blocked_exercises.map(b => `<li><strong>${this.escapeHtml(b.exercise || '')}:</strong> ${this.escapeHtml(b.reason || '')}</li>`).join('')}
              </ul>
            </div>
          `;
          blockedCont.classList.remove('d-none');
        } else {
          blockedCont.classList.add('d-none');
        }
      }
    } catch (exErr) {
      console.error('Error rendering exercise section:', exErr);
    }
  }

  getFallbackWeekSchedule(messCat) {
    const isJco = (messCat || '').toUpperCase().includes('JCO');
    if (isJco) {
      return {
        'Monday': { meals: { 'Breakfast': [{ food_item: 'Paratha', portion: '2 pcs (~180 g)' }, { food_item: 'Curd / Dahi', portion: '100 g' }, { food_item: 'Boiled Egg', portion: '2 eggs' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Tadka', portion: '150 g' }, { food_item: 'Mix Veg', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Chicken Curry / Paneer', portion: '140 g' }] } },
        'Tuesday': { meals: { 'Breakfast': [{ food_item: 'Idli / Dosa', portion: '180 g' }, { food_item: 'Sambar', portion: '120 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Jeera Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Rajma', portion: '150 g' }, { food_item: 'Seasonal Veg', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Mutton / Paneer Lababdar', portion: '140 g' }] } },
        'Wednesday': { meals: { 'Breakfast': [{ food_item: 'Poha / Upma', portion: '180 g' }, { food_item: 'Boiled Chana', portion: '60 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Makhani', portion: '150 g' }, { food_item: 'Bhindi Fry', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Fish / Soyabean Curry', portion: '140 g' }] } },
        'Thursday': { meals: { 'Breakfast': [{ food_item: 'Puri Sabji', portion: '4 pcs (~160 g)' }, { food_item: 'Halwa', portion: '50 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Arhar', portion: '150 g' }, { food_item: 'Aloo Matar', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Chicken Do Pyaza / Paneer', portion: '140 g' }] } },
        'Friday': { meals: { 'Breakfast': [{ food_item: 'Bread Omelet / Cutlet', portion: '2 pcs (~160 g)' }, { food_item: 'Fruit', portion: '100 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Mix Dal', portion: '150 g' }, { food_item: 'Seasonal Veg', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Egg Curry / Malai Kofta', portion: '140 g' }] } },
        'Saturday': { meals: { 'Breakfast': [{ food_item: 'Stuffed Paratha', portion: '2 pcs (~180 g)' }, { food_item: 'Curd / Dahi', portion: '100 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Veg Pulao', portion: '180 g' }, { food_item: 'Chapati', portion: '2 pcs (~60 g)' }, { food_item: 'Kadhi', portion: '150 g' }, { food_item: 'Aloo Jeera', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Chicken / Paneer Butter Masala', portion: '140 g' }] } },
        'Sunday': { meals: { 'Breakfast': [{ food_item: 'Chole Bhature', portion: '2 pcs (~220 g)' }, { food_item: 'Sweet Lassi / Tea', portion: '180 ml' }], 'Lunch': [{ food_item: 'Dum Biryani', portion: '240 g' }, { food_item: 'Raita', portion: '100 g' }, { food_item: 'Salad', portion: '60 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Makhani', portion: '150 g' }, { food_item: 'Shahi Paneer / Mutton', portion: '150 g' }] } }
      };
    }
    return {
      'Monday': { meals: { 'Breakfast': [{ food_item: 'Poori', portion: '4 pcs (~120 g)' }, { food_item: 'Aloo Bhaji', portion: '150 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Tea': [{ food_item: 'Namkeen / Biscuits', portion: '30 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Green Veg', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Chicken / Paneer', portion: '120 g' }] } },
      'Tuesday': { meals: { 'Breakfast': [{ food_item: 'Idli / Dosa', portion: '180 g' }, { food_item: 'Sambar', portion: '120 g' }, { food_item: 'Boiled Egg', portion: '2 eggs' }], 'Tea': [{ food_item: 'Roasted Chana', portion: '35 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Rajma', portion: '150 g' }, { food_item: 'Bhindi', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Egg Curry / Paneer', portion: '120 g' }] } },
      'Wednesday': { meals: { 'Breakfast': [{ food_item: 'Poha / Upma', portion: '180 g' }, { food_item: 'Boiled Egg', portion: '1 egg' }, { food_item: 'Tea', portion: '150 ml' }], 'Tea': [{ food_item: 'Bread Pakoda / Samosa', portion: '50 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Makhani', portion: '150 g' }, { food_item: 'Mix Veg', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Fish / Soyabean Curry', portion: '120 g' }] } },
      'Thursday': { meals: { 'Breakfast': [{ food_item: 'Stuffed Paratha', portion: '2 pcs (~180 g)' }, { food_item: 'Dahi / Curd', portion: '100 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Tea': [{ food_item: 'Biscuits / Mathri', portion: '35 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Arhar', portion: '150 g' }, { food_item: 'Aloo Gobi', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Chicken / Paneer Bhurji', portion: '120 g' }] } },
      'Friday': { meals: { 'Breakfast': [{ food_item: 'Bread Omelet / Cutlet', portion: '2 pcs (~140 g)' }, { food_item: 'Banana', portion: '1 pc (~100 g)' }, { food_item: 'Tea', portion: '150 ml' }], 'Tea': [{ food_item: 'Roasted Peanuts / Chana', portion: '35 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Chana Dal', portion: '150 g' }, { food_item: 'Seasonal Veg', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Egg Curry / Kofta', portion: '120 g' }] } },
      'Saturday': { meals: { 'Breakfast': [{ food_item: 'Daliya / Khichdi', portion: '180 g' }, { food_item: 'Boiled Egg', portion: '1 egg' }, { food_item: 'Tea', portion: '150 ml' }], 'Tea': [{ food_item: 'Poha / Snacks', portion: '40 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Kadhi Pakoda', portion: '150 g' }, { food_item: 'Aloo Baingan', portion: '140 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal', portion: '150 g' }, { food_item: 'Chicken / Paneer Butter Masala', portion: '120 g' }] } },
      'Sunday': { meals: { 'Breakfast': [{ food_item: 'Chole Bhature', portion: '2 pcs (~200 g)' }, { food_item: 'Tea / Milk', portion: '150 ml' }], 'Tea': [{ food_item: 'Pakoda / Samosa', portion: '50 g' }, { food_item: 'Tea', portion: '150 ml' }], 'Lunch': [{ food_item: 'Special Biryani', portion: '220 g' }, { food_item: 'Raita / Curd', portion: '100 g' }, { food_item: 'Salad', portion: '60 g' }], 'Dinner': [{ food_item: 'Rice', portion: '150 g' }, { food_item: 'Chapati', portion: '3 pcs (~90 g)' }, { food_item: 'Dal Makhani', portion: '150 g' }, { food_item: 'Sweet / Kheer', portion: '60 g' }] } }
    };
  }

  switchMessDay(dayName) {
    try {
      const diet = this.currentDiet || {};
      let weekly = diet.weekly_schedule || {};
      const messCat = diet.mess_category || 'OR MESS';
      const activeDay = diet.day_of_week || 'Monday';

      // Fallback if weekly_schedule is missing or empty
      if (!weekly || Object.keys(weekly).length === 0) {
        if (Array.isArray(diet.weekly_schedule_list) && diet.weekly_schedule_list.length > 0) {
          weekly = {};
          diet.weekly_schedule_list.forEach(d => {
            if (d && d.day) weekly[d.day] = d;
          });
        } else {
          weekly = this.getFallbackWeekSchedule(messCat);
        }
      }

      // Update pill buttons active state
      document.querySelectorAll('.rec-day-pill').forEach(btn => {
        const bDay = (btn.getAttribute('data-day') || '').toLowerCase();
        if (bDay === (dayName || '').toLowerCase()) {
          btn.classList.add('active', 'btn-primary');
          btn.classList.remove('btn-outline-primary');
        } else {
          btn.classList.remove('active', 'btn-primary');
          btn.classList.add('btn-outline-primary');
        }
      });

      const container = document.getElementById('recMenuTableContainer');
      if (!container) return;

      if ((dayName || '').toLowerCase() === 'full') {
        container.innerHTML = this.renderFullWeekTable(weekly, activeDay, messCat, this.currentSoldier || {});
      } else {
        const dayData = weekly[dayName] || weekly['Monday'] || {};
        container.innerHTML = this.renderSingleDayTable(dayName, dayData);
      }
    } catch (e) {
      console.error('Error switching mess day:', e);
    }
  }

  renderFullWeekTable(weeklySchedule, activeDay = '', messCat = 'OR MESS', soldier = {}) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const fallback = this.getFallbackWeekSchedule(messCat);
    const weekly = (weeklySchedule && Object.keys(weeklySchedule).length > 0) ? weeklySchedule : fallback;

    const currentSol = soldier && soldier.rank ? soldier : (this.currentSoldier || {});
    const sRank = (currentSol.rank || '').toUpperCase();
    const sArmyNo = (currentSol.army_number || '').toUpperCase();
    const isJc = (messCat || '').toUpperCase().includes('JCO') ||
                 sArmyNo.includes('JC') ||
                 ['SUBEDAR', 'SUB', 'NB SUB', 'HONY', 'HONORARY'].some(r => sRank.includes(r));

    const rows = days.map((dName, idx) => {
      const dData = weekly[dName] || fallback[dName] || {};
      const isToday = (activeDay && dName.toLowerCase() === activeDay.toLowerCase());
      const meals = dData.meals || {};

      const formatMealCell = (mKey) => {
        const items = meals[mKey] || [];
        if (!Array.isArray(items) || items.length === 0) {
          return '<span class="text-muted small fst-italic">--</span>';
        }
        return items.map(it => {
          let name = '';
          let portion = '';
          if (typeof it === 'string') {
            const parts = it.split(':');
            name = parts[0] ? parts[0].trim() : it;
            portion = parts[1] ? parts[1].trim() : '';
          } else {
            name = it.food_item || it.item || 'Item';
            portion = it.portion || it.quantity || '';
          }
          return `
            <div class="d-flex align-items-center justify-content-between gap-1 py-1 mb-1 border-bottom" style="border-bottom-style: dashed !important; font-size: 0.82rem;">
              <span class="fw-bold text-dark">${this.escapeHtml(name)}</span>
              <span class="badge bg-white text-primary border border-primary-subtle fw-bold font-monospace shadow-xs px-2 py-0.5" style="font-size: 0.76rem; white-space: nowrap;">
                ${this.escapeHtml(portion)}
              </span>
            </div>
          `;
        }).join('');
      };

      return `
        <tr>
          <td class="ps-3 align-top py-2.5">
            <div class="fw-bold text-dark" style="font-size: 0.95rem;">${dName}</div>
            <div class="small text-muted font-monospace" style="font-size: 0.75rem;">Day ${idx + 1} of Cycle</div>
          </td>
          <td class="align-top py-2.5">${formatMealCell('Breakfast')}</td>
          ${!isJc ? `<td class="align-top py-2.5">${formatMealCell('Tea')}</td>` : ''}
          <td class="align-top py-2.5">${formatMealCell('Lunch')}</td>
          <td class="align-top pe-3 py-2.5">${formatMealCell('Dinner')}</td>
        </tr>
      `;
    }).join('');

    return `
      <div class="border rounded bg-white shadow-sm overflow-hidden">
        <table class="table table-sm table-bordered table-hover mb-0 align-middle">
          <thead class="table-light">
            <tr style="font-size: 0.84rem;">
              <th style="width: ${isJc ? '15%' : '14%'};" class="ps-3 text-uppercase text-muted py-2"><i class="fas fa-calendar-day me-1"></i> Day &amp; Rotation</th>
              <th style="width: ${isJc ? '27%' : '22%'};" class="text-uppercase text-primary py-2"><i class="fas fa-sun text-warning me-1"></i> Breakfast (Portion)</th>
              ${!isJc ? `<th style="width: 18%;" class="text-uppercase text-secondary py-2"><i class="fas fa-mug-hot text-secondary me-1"></i> Tea / Refreshment</th>` : ''}
              <th style="width: ${isJc ? '29%' : '23%'};" class="text-uppercase text-success py-2"><i class="fas fa-drumstick-bite text-success me-1"></i> Lunch (Grams)</th>
              <th style="width: ${isJc ? '29%' : '23%'}; color: #4f46e5;" class="pe-3 text-uppercase py-2"><i class="fas fa-moon me-1" style="color: #4f46e5;"></i> Dinner (Grams)</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
  }

  renderSingleDayTable(dayName, dayData) {
    const meals = dayData.meals || {};
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
        const items = meals[k] || [];
        const itemsHtml = items.map(it => {
          const name = typeof it === 'string' ? it : (it.food_item || it.item || 'Item');
          const portion = typeof it === 'string' ? '' : (it.portion || it.quantity || '');
          return `
            <div class="d-inline-flex align-items-center gap-2 p-2 border rounded bg-light me-2 mb-2">
              <span class="fw-bold text-dark">${this.escapeHtml(name)}</span>
              ${portion ? `<span class="badge bg-primary font-monospace">${this.escapeHtml(portion)}</span>` : ''}
            </div>
          `;
        }).join('');
        return `
          <tr>
            <td class="fw-bold text-primary ps-3 align-middle" style="width: 20%; font-size: 0.9rem;">${this.escapeHtml(k)} (${this.escapeHtml(dayName)})</td>
            <td class="pe-3 align-middle">${itemsHtml}</td>
          </tr>
        `;
      }).join('');
    } else {
      rowsHtml = `<tr><td colspan="2" class="text-center text-muted py-3">No meal data available for ${this.escapeHtml(dayName)}.</td></tr>`;
    }

    return `
      <div class="border rounded bg-white shadow-sm overflow-hidden p-2">
        <table class="table table-sm table-hover mb-0 align-middle">
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    `;
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
  window.FitnessTrendDashboard = {
    switchMessDay: (day) => {
      if (window.fitnessApp) {
        window.fitnessApp.switchMessDay(day);
      }
    },
    openCalculateAllConfirmation: () => window.fitnessApp?.openCalculateAllConfirmation(),
    executeCalculateAllFitness: () => window.fitnessApp?.executeCalculateAllFitness()
  };
  window.FitnessDashboard = window.FitnessTrendDashboard;
});
