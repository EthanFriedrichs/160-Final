create database accounts;
use accounts;

drop table base_user;
create table base_user (email_address varchar(255) primary key, user_password varchar(255));
select * from base_user;
insert into base_user values ("student1", "exampleStudent"), ("teacher1", "exampleTeacher");

drop table students;
create table students (student_id int primary key auto_increment, email_address varchar(255), foreign key (email_address) references base_user(email_address));
select * from students;
insert into students (email_address) values ("student1");

drop table teachers;
create table teachers (teacher_id int primary key auto_increment, email_address varchar(255), foreign key (email_address) references base_user(email_address));
select * from teachers;
insert into teachers (email_address) values ("teacher1");

drop table tests;
create table tests (test_id int primary key auto_increment, test_name varchar(255), email_address varchar(255), foreign key (email_address) references base_user(email_address));
select * from tests;
insert into tests (test_name, email_address) values 
("Test_test1", "Teacher"),
("Test_test2", "Teacher"),
("Test_test3", "Teacher");
update tests set test_name = "Test_test2" where test_id = 2;

drop table questions;
create table questions (question_id int auto_increment, question_name varchar(255), test_id int,
primary key (question_id, test_id));
select * from questions;
insert into questions (question_name, test_id) values ("Q1A", 2), ("Q2A", 2), ("Q3A", 2);
update questions set question_name = "Q1A", test_id = 2 where question_id = 1;

drop table test_answer;
create table test_answer (answer_id int auto_increment primary key, answer varchar(255), question_id int, email_address varchar(255), test_taken_id int,
foreign key (question_id) references questions(question_id),
foreign key (email_address) references base_user(email_address),
foreign key (test_taken_id) references test_taken(test_taken_id));
select * from test_answer;
insert into test_answer (answer, question_id, email_address) values ("Cool", 1, "brennanStudent");

drop table test_taken;
create table test_taken (test_taken_id int primary key auto_increment, test_id int, email_address varchar(255),
foreign key (test_id) references tests(test_id),
foreign key (email_address) references base_user(email_address));
select * from test_taken;

drop table grades;
create table grades (grade_id int primary key auto_increment, grade int, email_address varchar(255), test_taken_id int,
foreign key (email_address) references base_user(email_address),
foreign key (test_taken_id) references test_taken(test_taken_id));
select * from grades;
insert into grades (grade, email_address, test_taken_id) values (100, "brennanStudent", 1);
select grade_id, grade, test_name, grades.email_address from grades join test_taken on (test_taken.test_taken_id = grades.test_taken_id) join tests on (tests.test_id = test_taken.test_id) having grades.email_address = "brennanStudent";

select * from test_answer join questions on (test_answer.question_id = questions.question_id) having test_taken_id = 1;
select test_id, test_name from tests where email_address = "brennanStudent" and test_id not in (select test_id from test_taken where email_address = "brennanStudent");
select test_name, grades.email_address, grade, tests.email_address from tests join test_taken on (test_taken.test_id = tests.test_id) join grades on (grades.test_taken_id = test_taken.test_taken_id);

select test_id, test_name from tests where email_address = "Teacher" and test_id not in (select test_id from test_taken where email_address = "brennanStudent") and 0 != (select count(question_id) from questions where test_id = 2);