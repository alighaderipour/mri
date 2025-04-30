use mri
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    national_code VARCHAR(10),
    first_name NVARCHAR(15) NOT NULL,
    last_name NVARCHAR(25) NOT NULL,
	phone_number nvarchar (11) not null,
    section NVARCHAR(20) NOT NULL,
    is_admin BIT DEFAULT 0,
    can_assign_turn BIT DEFAULT 0,
    is_active BIT DEFAULT 1
);

CREATE TABLE mri_requests (
    id INT IDENTITY(1,1) PRIMARY KEY,
    reservation_date DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    user_id INT FOREIGN KEY (user_id) REFERENCES users(id),
    applicant_national_id NVARCHAR(10) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    application_first_name NVARCHAR(30),
    application_last_name NVARCHAR(30),
    application_phone_number NVARCHAR(11) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    application_section NVARCHAR(30) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    patient_name NVARCHAR(30) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    patient_phone_number NVARCHAR(11) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    patient_insurance_name NVARCHAR(20) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    tracking_code NVARCHAR(6) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
    explanation NVARCHAR(100) COLLATE Arabic_100_CI_AI_SC_UTF8 NOT NULL,
	has_requested_site bit default 0,
    submitted_date DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    submitted_hour TIME NOT NULL DEFAULT CAST(GETDATE() AS TIME),
    turn_date DATE NULL,
    turn_hour TIME NULL,
    insurance_number bit,
    uploaded_image_path nvarchar(max) null
);


create table insurances
(id int, name nvarchar(30), image_required bit)


insert into insurances
values 
(1, N'نیروهای مسلح' , 0),
(2, N'تامین اجتماعی' , 0),
(3, N'خدمات درمانی - سلامت' , 0),
(4, N'سایر' , 1)


insert into users (  username ,password_hash  ,national_code  ,first_name  ,last_name , phone_number ,section  ,
is_admin  ,can_assign_turn ,is_active)
values ('admin' , 'scrypt:32768:8:1$mCO52UTrXvFJikU9$9f40a57b978a5082d1dfb64dd0ae7a03b7946ae714157519bbb2e48a072b9219efd8fbcf1adfc383accf86ae8f9efa0bdc362e282dc785a7f935596139c8f3fa' ,
'2980279315','علي','قادري پور', '09131958575','فاوا',1,1,1)



CREATE TABLE sections (
    section_nr INT PRIMARY KEY,
    name NVARCHAR(60) NOT NULL
);



create table pref(
id int identity (1,1) primary key ,
max_mri_reserve_day int ,
max_user_reserve_day int,
max_user_reserve_month int
)

insert into pref(max_mri_reserve_day, max_user_reserve_day,  max_user_reserve_month) values
(10,1,3)

