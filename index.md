USE hrms;

-- =========================================================================
-- INDEXES FOR DASHBOARD.HTML METRIC CARDS & BADGES
-- =========================================================================

-- 1. Optimize Dashboard Interview & JCO State Filtering Queries
CREATE INDEX idx_personnel_comp_home_state ON personnel(company, home_state);
CREATE INDEX idx_personnel_td_company ON personnel(td_status, company);

-- 2. Optimize Tasks Dashboard Queries
CREATE INDEX idx_tasks_assigned_status ON tasks(assigned_to, task_status);

-- 3. Optimize Active Courses Date Range Queries
CREATE INDEX idx_courses_dates_army ON candidate_on_courses(course_starting_date, course_end_date, army_number);

-- 4. Optimize Loans & Sensitive Reason Log Queries
CREATE INDEX idx_loans_army_number ON loans(army_number);
CREATE INDEX idx_sensitive_log_army_date ON sensitive_reason_log(army_number, added_on);
CREATE INDEX idx_sensitive_marking_army ON sensitive_marking(army_number, marked_on);

-- 5. Optimize Roll Call Points Status Queries
CREATE INDEX idx_rollcall_status ON roll_call_points(status);

-- 6. Optimize Projects Company Filter Queries
CREATE INDEX idx_projects_company ON projects(company);

-- 7. Optimize Today Events Alarm Queries
CREATE INDEX idx_event_alarm_date ON today_event_alarm(event_date);

-- 8. Optimize Graph APIs (get_posted_strength & get_detachment_stats_for_graph)
CREATE INDEX idx_personnel_company_rank ON personnel(company, `rank`);
CREATE INDEX idx_assigned_det_status_army ON assigned_det(det_status, army_number, det_id);
CREATE INDEX idx_personnel_det_status_company ON personnel(detachment_status, company, army_number);

