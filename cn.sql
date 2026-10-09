show databases;

create database email_client;
use email_client;

select * from email_client;

use email_client;
show tables;

select *from users;
select *from emails;
select *from attachments;
select *from recipients;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE attachments;
TRUNCATE TABLE recipients;
TRUNCATE TABLE emails;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM emails;
SELECT COUNT(*) FROM attachments;
SELECT COUNT(*) FROM recipients;

