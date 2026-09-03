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
    this.goalSelect = document.getElementById('fitnessGoalSelect');
    this.langSelect = document.getElementById('fitnessLangSelect');
    this.stageNav = document.getElementById('workflowStageNav');
    this.activeSearchIndex = -1;
    
    // Ensure export button is disabled initially
    if (this.pdfBtn) this.pdfBtn.disabled = true;
    
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
      if (this.searchResults.children.length > 0) {
        this.searchResults.classList.remove('d-none');
      } else {
        this.performSearch(this.searchInput.value.trim(), true);
      }
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
        this.searchResults.classList.add('d-none');
        this.currentArmyNumber = null;
        this.currentData = null;
        if (this.pdfBtn) this.pdfBtn.disabled = true;
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

    // PDF Download button
    const pdfBtn = document.getElementById('downloadPdfBtn');
    if (pdfBtn) {
      pdfBtn.addEventListener('click', () => {
        if (!this.currentArmyNumber) return;

        const originalHtml = pdfBtn.innerHTML;
        pdfBtn.disabled = true;
        pdfBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Exporting...`;

        const lang = this.currentLang || (this.langSelect ? this.langSelect.value : 'en');
        const pdfUrl = `/fitness/report/pdf/${encodeURIComponent(this.currentArmyNumber)}?goal=${encodeURIComponent(this.currentGoal)}&lang=${encodeURIComponent(lang)}`;
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        setTimeout(() => {
          pdfBtn.disabled = false;
          pdfBtn.innerHTML = originalHtml;
        }, 2500);
      });
    }

    // Retrain modal trigger
    const retrainBtn = document.getElementById('triggerRetrainBtn');
    if (retrainBtn) {
      retrainBtn.addEventListener('click', () => this.triggerModelRetrain());
    }
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
    try {
      const res = await fetch(`/fitness/api/personnel-list?q=${encodeURIComponent(query)}&limit=15`);
      const json = await res.json();
      if (json.success) {
        this.renderSearchResults(json.data, showDropdown);
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

  getInitials(name) {
    if (!name) return 'SO';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  renderSearchResults(soldiers, showDropdown = true) {
    this.searchResults.innerHTML = '';
    this.activeSearchIndex = -1;

    if (!soldiers || soldiers.length === 0) {
      this.searchResults.innerHTML = `
        <div class="p-3 text-muted text-center small">
          <i class="fas fa-search me-1"></i> No personnel found matching query.
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

      item.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="search-soldier-avatar">${initials}</div>
          <div>
            <div class="fw-bold" style="color: var(--fit-text-main); font-size: 0.95rem;">
              ${s.name} <span class="badge bg-secondary ms-1 fw-normal" style="font-size: 0.72rem;">${s.rank || 'Soldier'}</span>
            </div>
            <div class="small text-muted d-flex align-items-center gap-2 mt-1">
              <span class="search-soldier-army-no">${s.army_number}</span>
              <span>&bull;</span>
              <span>${s.company || 'Unit HQ'}</span>
              <span>&bull;</span>
              <span>${s.trade || 'GD'}</span>
            </div>
          </div>
        </div>
        <div class="text-end">
          <span class="badge ${badgeClass} text-uppercase mb-1" style="font-size: 0.72rem;">${statusText}</span>
          <div class="small text-muted fw-bold">${s.weight ? s.weight + ' kg' : 'Wt: --'}</div>
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
        this.errorAlert.textContent = json.error || 'Failed to analyze soldier records.';
        this.errorAlert.classList.remove('d-none');
        return;
      }

      this.currentData = json;
      if (this.pdfBtn) this.pdfBtn.disabled = false;
      this.renderAllStages(json);
      this.activeContent.classList.remove('d-none');
      this.switchStage(this.activeStage);
    } catch (e) {
      if (this.pdfBtn) this.pdfBtn.disabled = true;
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
    document.getElementById('profWeightDiff').textContent = s.weight_difference_kg !== null ? `${s.weight_difference_kg > 0 ? '+' : ''}${s.weight_difference_kg} kg` : 'N/A';
    
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
    
    document.getElementById('anaWeightStatus').textContent = s.weight_status || 'N/A';
    document.getElementById('anaWeightDev').textContent = s.weight_deviation_percent !== null ? `${s.weight_deviation_percent > 0 ? '+' : ''}${s.weight_deviation_percent}%` : 'N/A';
    document.getElementById('anaWeightDiffKg').textContent = s.weight_difference_kg !== null ? `${s.weight_difference_kg > 0 ? '+' : ''}${s.weight_difference_kg} kg` : 'N/A';
    
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
    const strengthsCont = document.getElementById('predStrengthsList');
    strengthsCont.innerHTML = (pred.strengths || []).map(str => `
      <li class="factor-item strength">
        <i class="fas fa-check-circle factor-icon text-success"></i>
        <span>${str}</span>
      </li>
    `).join('');
    
    // Improvements
    const improveCont = document.getElementById('predImprovementsList');
    improveCont.innerHTML = (pred.improvements || []).map(imp => `
      <li class="factor-item improvement">
        <i class="fas fa-arrow-circle-up factor-icon text-warning"></i>
        <span>${imp}</span>
      </li>
    `).join('');

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
            <span class="milestone-badge bg-${m.badge}">${m.days === 0 ? 'Baseline' : `+${m.days} Days`}</span>
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
          labels: prog.chart_data.labels,
          datasets: [
            {
              label: 'Readiness Score (0-100)',
              data: prog.chart_data.score_series,
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              fill: true,
              tension: 0.3,
              yAxisID: 'yScore'
            },
            {
              label: 'Projected Weight (kg)',
              data: prog.chart_data.weight_series,
              borderColor: '#3b82f6',
              borderDash: [5, 5],
              fill: false,
              tension: 0.3,
              yAxisID: 'yWeight'
            }
          ]
        },
        options: {
          responsive: true,
          scales: {
            yScore: {
              type: 'linear',
              position: 'left',
              min: 40,
              max: 100,
              title: { display: true, text: 'Readiness Score' }
            },
            yWeight: {
              type: 'linear',
              position: 'right',
              grid: { drawOnChartArea: false },
              title: { display: true, text: 'Body Weight (kg)' }
            }
          }
        }
      });
    }
  }

  renderReportPreview(data) {
    const previewCont = document.getElementById('reportHtmlPreviewCont');
    if (!previewCont) return;

    const s = data.soldier;
    const pred = data.prediction;
    const rec = data.recommendations;
    const prog = data.progression;

    previewCont.innerHTML = `
      <div class="card p-4 shadow-sm border" style="background: white; color: #1e293b; max-width: 900px; margin: 0 auto; font-family: 'Segoe UI', Arial, sans-serif;">
        <div class="text-center pb-3 border-bottom mb-3">
          <h4 class="fw-bold mb-1" style="color: #1b382b;">15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM</h4>
          <h5 class="fw-bold text-primary mb-1">INDIVIDUAL FITNESS PREDICTION &amp; PERSONALIZED FITNESS REPORT</h5>
          <div class="small text-muted">Generated: ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })} hrs &bull; Model: ${pred.model_version || 'v1'}</div>
        </div>

        <table class="table table-bordered table-sm mb-3" style="font-size: 0.88rem;">
          <tr style="background: #f1f5f9;">
            <th style="width: 20%;">Name</th><td>${s.name}</td>
            <th style="width: 20%;">Army Number</th><td>${s.army_number}</td>
          </tr>
          <tr>
            <th>Rank / Trade</th><td>${s.rank} / ${s.trade}</td>
            <th>Company / Section</th><td>${s.company} / ${s.section || 'N/A'}</td>
          </tr>
          <tr style="background: #f1f5f9;">
            <th>Height / Weight</th><td>${s.height_cm} cm / ${s.actual_weight_kg} kg</td>
            <th>Ideal Wt / Deviation</th><td>${s.ideal_weight_kg} kg (${s.weight_deviation_percent > 0 ? '+' : ''}${s.weight_deviation_percent}%)</td>
          </tr>
          <tr>
            <th>BMI &amp; Category</th><td>${s.bmi} (${s.bmi_category})</td>
            <th>BPET / PPT Grading</th><td>${s.bpet_grade || 'N/A'} / ${s.ppt_grade || 'N/A'}</td>
          </tr>
        </table>

        <div class="p-3 mb-3 rounded" style="background: rgba(59, 130, 246, 0.08); border-left: 5px solid #3b82f6;">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <div class="small text-muted text-uppercase fw-bold">AI Physical Readiness Prediction</div>
              <h3 class="fw-bold mb-0 text-primary">${pred.fitness_score} / 100 &mdash; ${pred.category_label}</h3>
            </div>
            <div class="text-end">
              <span class="badge bg-primary fs-6">Confidence: ${pred.confidence_score}%</span>
            </div>
          </div>
        </div>

        <div class="row mb-3">
          <div class="col-6">
            <h6 class="fw-bold text-success mb-2"><i class="fas fa-check-circle me-1"></i> Key Positive Factors:</h6>
            <ul class="small ps-3 mb-0">${(pred.strengths || []).map(str => `<li>${str}</li>`).join('')}</ul>
          </div>
          <div class="col-6">
            <h6 class="fw-bold text-warning mb-2"><i class="fas fa-arrow-circle-up me-1"></i> Priority Action Areas:</h6>
            <ul class="small ps-3 mb-0">${(pred.improvements || []).map(imp => `<li>${imp}</li>`).join('')}</ul>
          </div>
        </div>

        <hr class="my-3">
        <h6 class="fw-bold text-primary mb-2"><i class="fas fa-utensils me-1"></i> 4. Personalized Dietary &amp; Macronutrient Plan (${rec.diet.target_calories} kcal / Day):</h6>
        <div class="row g-2 mb-2 text-center">
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">COMPLEX CARBS</small>
              <strong class="text-success" style="color: #10b981 !important; font-size: 0.95rem;">${rec.diet.macros.carb_grams}g (${rec.diet.macros.carb_pct}%)</strong>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">HEALTHY FATS</small>
              <strong class="text-warning" style="color: #f59e0b !important; font-size: 0.95rem;">${rec.diet.macros.fat_grams}g (${rec.diet.macros.fat_pct}%)</strong>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">DAILY PROTEIN</small>
              <strong class="text-primary" style="color: #3b82f6 !important; font-size: 0.95rem;">${rec.diet.macros.protein_grams}g (${rec.diet.macros.protein_pct}%)</strong>
            </div>
          </div>
          <div class="col-3">
            <div class="p-2 border rounded bg-light">
              <small class="text-muted d-block fw-bold" style="font-size: 0.72rem;">HYDRATION</small>
              <strong class="text-info" style="color: #06b6d4 !important; font-size: 0.95rem;">${rec.diet.hydration_liters} L / Day</strong>
            </div>
          </div>
        </div>
        <p class="small text-muted mb-3">${rec.diet.strategy}</p>

        <h6 class="fw-bold text-primary mb-2 mt-2"><i class="fas fa-running me-1"></i> 5. Physical Training:</h6>
        <p class="small text-muted mb-2">${rec.exercise.title} &mdash; ${rec.exercise.focus_area}</p>
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
