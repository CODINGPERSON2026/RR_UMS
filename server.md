# Date 10 JUNE 


INSERT INTO leave_details (
    army_number,
    personnel_id,
    year,
    AL, CL, AAL, PL, `Annual Leave`,
    leave_start_date,
    leave_end_date,
    created_at
)
SELECT
    lsi.army_number,
    p.id AS personnel_id,
    YEAR(lsi.from_date) AS year,
    CASE WHEN lsi.leave_type = 'AL'           THEN DATEDIFF(lsi.to_date, lsi.from_date) + 1 ELSE 0 END AS AL,
    CASE WHEN lsi.leave_type = 'CL'           THEN DATEDIFF(lsi.to_date, lsi.from_date) + 1 ELSE 0 END AS CL,
    CASE WHEN lsi.leave_type = 'AAL'          THEN DATEDIFF(lsi.to_date, lsi.from_date) + 1 ELSE 0 END AS AAL,
    CASE WHEN lsi.leave_type = 'PL'           THEN DATEDIFF(lsi.to_date, lsi.from_date) + 1 ELSE 0 END AS PL,
    CASE WHEN lsi.leave_type = 'Annual Leave' THEN DATEDIFF(lsi.to_date, lsi.from_date) + 1 ELSE 0 END AS `Annual Leave`,
    lsi.from_date,
    lsi.to_date,
    NOW()
FROM leave_status_info lsi
INNER JOIN personnel p ON p.army_number = lsi.army_number
WHERE NOT EXISTS (
    SELECT 1 FROM leave_details ld
    WHERE ld.army_number = lsi.army_number
)
AND lsi.request_sent_to = 'Approved';


## step 2 delete from leave_status_info which are not exisiting in personnel table

-- Check count first
SELECT COUNT(*)
FROM leave_status_info
WHERE NOT EXISTS (
    SELECT 1 FROM personnel p
    WHERE p.army_number = TRIM(leave_status_info.army_number)
);

-- 
DELETE FROM leave_status_info
WHERE NOT EXISTS (
    SELECT 1 FROM personnel p
    WHERE p.army_number = TRIM(leave_status_info.army_number)
);








# 9 JUNE
SHOW EVENTS FROM hrms1;

check the events first



use hrms;
DELIMITER $$

ALTER EVENT update_course_status
ON SCHEDULE EVERY 1 DAY
STARTS '2026-04-28 00:00:00'
ON COMPLETION NOT PRESERVE
ENABLE
DO
BEGIN

    UPDATE candidate_on_courses
    SET status =
        CASE
            WHEN course_end_date < CURDATE() THEN 'Completed'
            WHEN CURDATE() BETWEEN course_starting_date AND course_end_date THEN 'Active'
            ELSE status
        END;

    UPDATE personnel p
    JOIN candidate_on_courses c
        ON p.army_number = c.army_number
    SET p.oncourse_status =
        CASE
            WHEN CURDATE() BETWEEN c.course_starting_date AND c.course_end_date
            THEN 1
            ELSE 0
        END;

END$$

DELIMITER ;




update 2 : 

UPDATE leave_details ld
JOIN personnel p
    ON TRIM(ld.army_number) = TRIM(p.army_number)
SET
    ld.`Annual Leave` = COALESCE(ld.`Annual Leave`, 0) + COALESCE(ld.AL, 0),
    ld.AL = 0
WHERE p.rank = 'Agniveer';










## UPDATE 3 
UPDATE leave_details ld
JOIN personnel p
    ON ld.army_number = p.army_number
SET ld.personnel_id = p.id;