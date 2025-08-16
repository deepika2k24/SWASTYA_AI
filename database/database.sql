CREATE DATABASE swastyaai;
use swastyaai;
 CREATE TABLE user(
    userid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL
 );

 CREATE TABLE bmi_records(
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    userid INT NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    bmi FLOAT NOT NULL,
    FOREIGN KEY (userid) REFERENCES user(userid) ON DELETE CASCADE 
 );

CREATE TABLE bp_sugar_records(
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    userid INT NOT NULL,
    systolic INT NOT NULL,
    diastolic INT NOT NULL,
    blood_sugar FLOAT NOT NULL,
    record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES user(userid) ON DELETE CASCADE
);

  CREATE TABLE teleconsultations (
        consult_id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT NOT NULL,
        pincode VARCHAR(10),
        city VARCHAR(100),
        FOREIGN KEY (user_id) REFERENCES user(userid) ON DELETE CASCADE
 );

CREATE TABLE suggested_hospitals (
        hospital_id INT AUTO_INCREMENT PRIMARY KEY,
        consult_id INT,
        hospital_name VARCHAR(255),
        address TEXT,
        FOREIGN KEY (consult_id) REFERENCES teleconsultations(consult_id)
     );





