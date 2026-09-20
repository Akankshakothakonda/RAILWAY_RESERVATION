-- ============================================
-- RAILWAY RESERVATION SYSTEM
-- Database: railway_db
-- ============================================

CREATE DATABASE IF NOT EXISTS railway_db;

USE railway_db;


-- ============================================
-- 1. USERS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    role VARCHAR(20) DEFAULT 'user'
);


-- ============================================
-- 2. TRAINS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS trains (
    train_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(20) UNIQUE NOT NULL,
    train_name VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    total_seats INT NOT NULL
);


-- ============================================
-- 3. PASSENGERS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
);


-- ============================================
-- 4. BOOKINGS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    train_id INT NOT NULL,
    passenger_id INT NOT NULL,
    journey_date DATE NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    pnr VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'CONFIRMED',

    FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    FOREIGN KEY (train_id)
        REFERENCES trains(train_id),

    FOREIGN KEY (passenger_id)
        REFERENCES passengers(passenger_id)
);


-- ============================================
-- 5. PAYMENTS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'SUCCESS',
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (booking_id)
        REFERENCES bookings(booking_id)
);


-- ============================================
-- SAMPLE TRAIN DATA
-- ============================================

INSERT IGNORE INTO trains
(train_number, train_name, source, destination,
 departure_time, arrival_time, total_seats)
VALUES

('12760', 'Charminar Express',
 'Hyderabad', 'Chennai',
 '18:00:00', '08:00:00', 120),

('17015', 'Visakha Express',
 'Secunderabad', 'Bhubaneswar',
 '17:00:00', '12:00:00', 100),

('12727', 'Godavari Express',
 'Visakhapatnam', 'Hyderabad',
 '20:00:00', '07:00:00', 120),

('12723', 'Telangana Express',
 'Hyderabad', 'New Delhi',
 '06:00:00', '06:30:00', 100),

('12786', 'Kacheguda Express',
 'Kacheguda', 'Bangalore',
 '18:30:00', '07:00:00', 110);


-- ============================================
-- SAMPLE USERS
-- ============================================

INSERT IGNORE INTO users
(name, email, password, phone, role)
VALUES
('Admin', 'admin@railway.com', 'admin123', '9000000000', 'admin'),

('Akanksha', 'akanksha@gmail.com', '12345', '9876543210', 'user');


-- ============================================
-- VERIFY TABLES
-- ============================================

SHOW TABLES;


-- ============================================
-- DISPLAY SAMPLE DATA
-- ============================================

SELECT * FROM users;

SELECT * FROM trains;

SELECT * FROM passengers;

SELECT * FROM bookings;

SELECT * FROM payments;