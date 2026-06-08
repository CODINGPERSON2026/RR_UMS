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