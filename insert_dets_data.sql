-- SQL to populate dets table for RR UMS
INSERT INTO `dets` (`det_id`, `det_name`) VALUES
(1, 'A COY DET'),
(2, 'B COY DET'),
(3, 'C COY DET'),
(4, 'D COY DET'),
(5, 'E COY DET'),
(6, 'F COY DET'),
(7, 'HQ COY DET'),
(8, 'COMM DET'),
(9, 'TACTICAL DET'),
(10, 'SECTOR HQ DET'),
(11, 'QRT DET'),
(12, 'ROAD OPENING DET')
ON DUPLICATE KEY UPDATE `det_name` = VALUES(`det_name`);
