-- Select your database first
USE hrms;

-- 1. Optimize Personnel & Rank Queries
CREATE INDEX idx_personnel_company ON personnel(company);
CREATE INDEX idx_personnel_rank ON personnel(`rank`);
CREATE INDEX idx_personnel_det_status ON personnel(detachment_status);

-- 2. Optimize Detachment Graph & Alarm Queries
CREATE INDEX idx_assigned_det_status ON assigned_det(det_status, army_number);
CREATE INDEX idx_assigned_det_id ON assigned_det(det_id);

-- 3. Optimize Today Schedules Queries
CREATE INDEX idx_schedules_date ON schedules(schedule_date);

-- 4. Optimize Weight System Queries
CREATE INDEX idx_weight_info_company ON weight_info(company);

-- 5. Optimize Unfit Medical Trend Queries
CREATE INDEX idx_monthly_medical_unit ON monthly_medical_status(unit, year, month);

-- 6. Optimize Sensitive Personnel Queries
CREATE INDEX idx_sensitive_marking_army ON sensitive_marking(army_number);

-- 7. Optimize Parade State Daily Dashboard Queries
CREATE INDEX idx_parade_state_date_company ON parade_state_daily(report_date, company);

-- 1. Accelerates leave pending alarm queries
CREATE INDEX idx_leave_status_updated ON leave_status_info(request_status, updated_at);

-- 2. Accelerates TD / attachment alarm queries
CREATE INDEX idx_td_date ON td_table(td_date);
CREATE INDEX idx_td_army_number ON td_table(army_number);

-- 3. Accelerates honours board queries
CREATE INDEX idx_hb_army_number ON honours_board(army_number);
