"""
Database Repository & Menu Catalog for Military Mess Facilities (OR & JCO).
Provides automatic Rank-to-Mess classification, menu lookup, and nutritional metadata.
"""

import os
import sys
import re
import logging
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger("fitness_trend.mess_menu_db")

try:
    from db_config import get_db_connection
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from db_config import get_db_connection


CREATE_MESS_MENUS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `ai_mess_menus` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `mess_type` VARCHAR(20) NOT NULL COMMENT 'OR or JCO',
    `day_of_week` VARCHAR(20) NOT NULL COMMENT 'Monday to Sunday',
    `meal_type` VARCHAR(20) NOT NULL COMMENT 'Breakfast, Tea, Lunch, Dinner',
    `food_item` VARCHAR(150) NOT NULL,
    `default_serving_unit` VARCHAR(50) DEFAULT 'g',
    `calories_per_100g` DECIMAL(6,2) DEFAULT 0.0,
    `protein_per_100g` DECIMAL(6,2) DEFAULT 0.0,
    `carb_per_100g` DECIMAL(6,2) DEFAULT 0.0,
    `fat_per_100g` DECIMAL(6,2) DEFAULT 0.0,
    `fiber_per_100g` DECIMAL(6,2) DEFAULT 0.0,
    `is_vegetarian` BOOLEAN DEFAULT TRUE,
    `is_protein_rich` BOOLEAN DEFAULT FALSE,
    `is_calorie_dense` BOOLEAN DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_mess_day_meal` (`mess_type`, `day_of_week`, `meal_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# ====================================================================
# MASTER SEED DATA FOR OR AND JCO MESS MENUS
# ====================================================================

# Standard nutritional metadata table for mess items (cal, protein, carb, fat, fiber per 100g or unit)
NUTRITION_LOOKUP = {
    # Grains & Breads
    "Rice": {"unit": "g", "cal": 130.0, "p": 2.7, "c": 28.2, "f": 0.3, "fib": 0.4, "veg": True, "protein_rich": False, "dense": False},
    "Lemon Rice": {"unit": "g", "cal": 145.0, "p": 2.8, "c": 27.5, "f": 2.5, "fib": 0.6, "veg": True, "protein_rich": False, "dense": False},
    "Jeera Rice": {"unit": "g", "cal": 140.0, "p": 2.8, "c": 27.0, "f": 2.2, "fib": 0.5, "veg": True, "protein_rich": False, "dense": False},
    "Rice Pulav": {"unit": "g", "cal": 150.0, "p": 3.2, "c": 26.5, "f": 3.2, "fib": 1.2, "veg": True, "protein_rich": False, "dense": False},
    "Veg Rice": {"unit": "g", "cal": 140.0, "p": 3.0, "c": 26.0, "f": 2.5, "fib": 1.5, "veg": True, "protein_rich": False, "dense": False},
    "Fried Rice": {"unit": "g", "cal": 160.0, "p": 3.5, "c": 28.0, "f": 4.0, "fib": 1.0, "veg": True, "protein_rich": False, "dense": False},
    "Chapati": {"unit": "pieces", "cal": 75.0, "p": 3.1, "c": 15.5, "f": 0.5, "fib": 2.4, "veg": True, "protein_rich": False, "dense": False},
    "Roti": {"unit": "pieces", "cal": 75.0, "p": 3.1, "c": 15.5, "f": 0.5, "fib": 2.4, "veg": True, "protein_rich": False, "dense": False},
    "Butter Roti": {"unit": "pieces", "cal": 105.0, "p": 3.2, "c": 15.5, "f": 3.8, "fib": 2.4, "veg": True, "protein_rich": False, "dense": True},
    "Rumali Roti": {"unit": "pieces", "cal": 110.0, "p": 3.5, "c": 22.0, "f": 1.2, "fib": 1.5, "veg": True, "protein_rich": False, "dense": False},
    "Missi Roti": {"unit": "pieces", "cal": 115.0, "p": 5.2, "c": 18.0, "f": 2.5, "fib": 3.2, "veg": True, "protein_rich": True, "dense": False},
    "Puri": {"unit": "pieces", "cal": 110.0, "p": 2.2, "c": 14.0, "f": 5.5, "fib": 1.0, "veg": True, "protein_rich": False, "dense": True},
    "Namkeen Puri": {"unit": "pieces", "cal": 115.0, "p": 2.4, "c": 14.5, "f": 5.8, "fib": 1.1, "veg": True, "protein_rich": False, "dense": True},
    "Plain Paratha": {"unit": "pieces", "cal": 190.0, "p": 4.5, "c": 26.0, "f": 8.0, "fib": 2.5, "veg": True, "protein_rich": False, "dense": True},
    "Porota": {"unit": "pieces", "cal": 190.0, "p": 4.5, "c": 26.0, "f": 8.0, "fib": 2.5, "veg": True, "protein_rich": False, "dense": True},
    "Aloo Paratha / Paneer Paratha / Muli Paratha": {"unit": "pieces", "cal": 220.0, "p": 6.5, "c": 28.0, "f": 9.5, "fib": 2.8, "veg": True, "protein_rich": True, "dense": True},
    "Chola Bhatura": {"unit": "pieces", "cal": 240.0, "p": 6.0, "c": 32.0, "f": 10.5, "fib": 3.0, "veg": True, "protein_rich": False, "dense": True},
    "Khichdi": {"unit": "g", "cal": 120.0, "p": 4.2, "c": 22.0, "f": 2.0, "fib": 2.2, "veg": True, "protein_rich": False, "dense": False},
    "Upma": {"unit": "g", "cal": 135.0, "p": 3.5, "c": 24.0, "f": 3.0, "fib": 1.8, "veg": True, "protein_rich": False, "dense": False},
    "Poha": {"unit": "g", "cal": 130.0, "p": 2.8, "c": 26.0, "f": 2.2, "fib": 1.5, "veg": True, "protein_rich": False, "dense": False},
    "Upma / Poha with Chutney": {"unit": "g", "cal": 140.0, "p": 3.2, "c": 25.0, "f": 3.2, "fib": 1.8, "veg": True, "protein_rich": False, "dense": False},
    "Daliya Wheat": {"unit": "g", "cal": 110.0, "p": 3.8, "c": 22.0, "f": 1.0, "fib": 3.5, "veg": True, "protein_rich": False, "dense": False},
    "South Indian / Chinese / Pav Bhaji / Chhola Bhatura with Sweet": {"unit": "g", "cal": 210.0, "p": 5.0, "c": 30.0, "f": 8.0, "fib": 2.0, "veg": True, "protein_rich": False, "dense": True},
    "Idli, Dosa, Uthappam": {"unit": "pieces", "cal": 130.0, "p": 3.8, "c": 26.0, "f": 1.5, "fib": 1.8, "veg": True, "protein_rich": False, "dense": False},
    "Biryani / Jeera Rice": {"unit": "g", "cal": 165.0, "p": 4.5, "c": 27.0, "f": 4.5, "fib": 1.5, "veg": True, "protein_rich": False, "dense": False},
    "Veg Biryani": {"unit": "g", "cal": 155.0, "p": 4.0, "c": 26.0, "f": 4.0, "fib": 2.0, "veg": True, "protein_rich": False, "dense": False},
    "Chicken Biryani": {"unit": "g", "cal": 180.0, "p": 12.0, "c": 23.0, "f": 5.5, "fib": 1.2, "veg": False, "protein_rich": True, "dense": False},

    # Dals & Legumes
    "Mix Dal": {"unit": "g", "cal": 95.0, "p": 6.5, "c": 14.5, "f": 1.8, "fib": 3.8, "veg": True, "protein_rich": True, "dense": False},
    "Dal": {"unit": "g", "cal": 90.0, "p": 6.0, "c": 14.0, "f": 1.5, "fib": 3.5, "veg": True, "protein_rich": True, "dense": False},
    "Dal Mix": {"unit": "g", "cal": 95.0, "p": 6.5, "c": 14.5, "f": 1.8, "fib": 3.8, "veg": True, "protein_rich": True, "dense": False},
    "Dal Mashri": {"unit": "g", "cal": 105.0, "p": 7.0, "c": 15.0, "f": 2.2, "fib": 4.0, "veg": True, "protein_rich": True, "dense": False},
    "Dal Mung": {"unit": "g", "cal": 88.0, "p": 6.8, "c": 13.5, "f": 1.2, "fib": 3.6, "veg": True, "protein_rich": True, "dense": False},
    "Dal Makhani": {"unit": "g", "cal": 130.0, "p": 5.8, "c": 14.0, "f": 6.0, "fib": 3.5, "veg": True, "protein_rich": True, "dense": True},
    "Dal Rajmah": {"unit": "g", "cal": 115.0, "p": 7.5, "c": 17.0, "f": 2.2, "fib": 5.0, "veg": True, "protein_rich": True, "dense": False},
    "Dal Arhar": {"unit": "g", "cal": 92.0, "p": 6.2, "c": 14.0, "f": 1.6, "fib": 3.5, "veg": True, "protein_rich": True, "dense": False},
    "Kadhi": {"unit": "g", "cal": 85.0, "p": 3.5, "c": 8.5, "f": 4.0, "fib": 1.0, "veg": True, "protein_rich": False, "dense": False},
    "Shambhar / Sambar": {"unit": "g", "cal": 65.0, "p": 3.2, "c": 10.0, "f": 1.2, "fib": 2.5, "veg": True, "protein_rich": False, "dense": False},
    "Sambar": {"unit": "g", "cal": 65.0, "p": 3.2, "c": 10.0, "f": 1.2, "fib": 2.5, "veg": True, "protein_rich": False, "dense": False},

    # Proteins (Chicken, Egg, Paneer, Fish, Soyabeen)
    "Chicken Curry": {"unit": "g", "cal": 155.0, "p": 16.5, "c": 4.2, "f": 8.2, "fib": 1.0, "veg": False, "protein_rich": True, "dense": False},
    "Fish Curry": {"unit": "g", "cal": 135.0, "p": 15.0, "c": 3.5, "f": 6.8, "fib": 0.8, "veg": False, "protein_rich": True, "dense": False},
    "Chicken Egg Curry": {"unit": "g", "cal": 160.0, "p": 15.5, "c": 4.0, "f": 9.0, "fib": 0.8, "veg": False, "protein_rich": True, "dense": False},
    "Egg Curry": {"unit": "g", "cal": 140.0, "p": 11.5, "c": 4.5, "f": 8.5, "fib": 0.8, "veg": False, "protein_rich": True, "dense": False},
    "Boiled Egg": {"unit": "pieces", "cal": 75.0, "p": 6.3, "c": 0.6, "f": 5.0, "fib": 0.0, "veg": False, "protein_rich": True, "dense": False},
    "Bread Omelet / Bread Cutlet": {"unit": "pieces", "cal": 180.0, "p": 8.5, "c": 18.0, "f": 8.0, "fib": 1.5, "veg": False, "protein_rich": True, "dense": True},
    "Egg Bhurji": {"unit": "g", "cal": 150.0, "p": 10.5, "c": 3.0, "f": 10.5, "fib": 0.5, "veg": False, "protein_rich": True, "dense": False},
    "Omelet": {"unit": "pieces", "cal": 140.0, "p": 9.5, "c": 2.0, "f": 10.0, "fib": 0.4, "veg": False, "protein_rich": True, "dense": False},
    "Mutter Paneer": {"unit": "g", "cal": 150.0, "p": 8.5, "c": 7.5, "f": 9.8, "fib": 2.2, "veg": True, "protein_rich": True, "dense": False},
    "Sahi Paneer": {"unit": "g", "cal": 175.0, "p": 8.0, "c": 8.5, "f": 12.5, "fib": 1.5, "veg": True, "protein_rich": True, "dense": True},
    "Palak Paneer": {"unit": "g", "cal": 135.0, "p": 8.2, "c": 5.5, "f": 9.2, "fib": 2.8, "veg": True, "protein_rich": True, "dense": False},
    "Paneer Chilli": {"unit": "g", "cal": 165.0, "p": 9.0, "c": 9.0, "f": 10.5, "fib": 1.8, "veg": True, "protein_rich": True, "dense": False},
    "01 x Special Paneer": {"unit": "g", "cal": 160.0, "p": 8.5, "c": 8.0, "f": 11.0, "fib": 1.8, "veg": True, "protein_rich": True, "dense": True},
    "Aloo Soyabeen / Aloo Rajma": {"unit": "g", "cal": 125.0, "p": 8.0, "c": 16.0, "f": 3.5, "fib": 3.8, "veg": True, "protein_rich": True, "dense": False},

    # Vegetables & Salads
    "Mix Veg": {"unit": "g", "cal": 70.0, "p": 2.5, "c": 9.5, "f": 2.5, "fib": 3.2, "veg": True, "protein_rich": False, "dense": False},
    "Seasonal Veg": {"unit": "g", "cal": 65.0, "p": 2.2, "c": 8.8, "f": 2.2, "fib": 3.0, "veg": True, "protein_rich": False, "dense": False},
    "Veg Curry": {"unit": "g", "cal": 75.0, "p": 2.4, "c": 9.0, "f": 3.2, "fib": 2.8, "veg": True, "protein_rich": False, "dense": False},
    "2 x Veg": {"unit": "g", "cal": 70.0, "p": 2.5, "c": 9.5, "f": 2.5, "fib": 3.2, "veg": True, "protein_rich": False, "dense": False},
    "01 x Veg": {"unit": "g", "cal": 70.0, "p": 2.5, "c": 9.5, "f": 2.5, "fib": 3.2, "veg": True, "protein_rich": False, "dense": False},
    "01 x Normal Veg": {"unit": "g", "cal": 65.0, "p": 2.2, "c": 8.8, "f": 2.2, "fib": 3.0, "veg": True, "protein_rich": False, "dense": False},
    "02 x Veg": {"unit": "g", "cal": 70.0, "p": 2.5, "c": 9.5, "f": 2.5, "fib": 3.2, "veg": True, "protein_rich": False, "dense": False},
    "1 x Veg Normal": {"unit": "g", "cal": 65.0, "p": 2.2, "c": 8.8, "f": 2.2, "fib": 3.0, "veg": True, "protein_rich": False, "dense": False},
    "01 x Mutter Mushroom": {"unit": "g", "cal": 80.0, "p": 4.2, "c": 9.0, "f": 3.0, "fib": 2.8, "veg": True, "protein_rich": False, "dense": False},
    "Puri & Sabji": {"unit": "g", "cal": 170.0, "p": 3.5, "c": 22.0, "f": 8.0, "fib": 2.5, "veg": True, "protein_rich": False, "dense": True},
    "Salad": {"unit": "g", "cal": 25.0, "p": 1.0, "c": 5.0, "f": 0.2, "fib": 2.5, "veg": True, "protein_rich": False, "dense": False},
    "Kachumber": {"unit": "g", "cal": 28.0, "p": 1.2, "c": 5.5, "f": 0.2, "fib": 2.6, "veg": True, "protein_rich": False, "dense": False},
    "Chutney": {"unit": "g", "cal": 45.0, "p": 1.2, "c": 6.5, "f": 1.8, "fib": 1.5, "veg": True, "protein_rich": False, "dense": False},
    "Papad": {"unit": "pieces", "cal": 35.0, "p": 2.0, "c": 6.0, "f": 0.5, "fib": 1.0, "veg": True, "protein_rich": False, "dense": False},
    "Karela Chips": {"unit": "g", "cal": 85.0, "p": 2.0, "c": 11.0, "f": 3.8, "fib": 3.5, "veg": True, "protein_rich": False, "dense": False},
    "Mirchi Fry": {"unit": "g", "cal": 60.0, "p": 1.5, "c": 7.0, "f": 3.0, "fib": 2.0, "veg": True, "protein_rich": False, "dense": False},
    "Dahi / Achar": {"unit": "g", "cal": 65.0, "p": 3.2, "c": 4.5, "f": 3.5, "fib": 0.2, "veg": True, "protein_rich": False, "dense": False},

    # Snacks & Tea
    "Bread Pakoda & Tea": {"unit": "serving", "cal": 240.0, "p": 5.5, "c": 32.0, "f": 10.0, "fib": 2.0, "veg": True, "protein_rich": False, "dense": True},
    "Bread Pakoda": {"unit": "pieces", "cal": 190.0, "p": 4.2, "c": 25.0, "f": 8.5, "fib": 1.8, "veg": True, "protein_rich": False, "dense": True},
    "Pakoda & Tea": {"unit": "serving", "cal": 210.0, "p": 4.5, "c": 26.0, "f": 9.5, "fib": 2.2, "veg": True, "protein_rich": False, "dense": True},
    "Pakoda": {"unit": "g", "cal": 160.0, "p": 3.5, "c": 20.0, "f": 8.0, "fib": 1.8, "veg": True, "protein_rich": False, "dense": True},
    "Poha & Tea": {"unit": "serving", "cal": 170.0, "p": 4.2, "c": 32.0, "f": 3.5, "fib": 1.8, "veg": True, "protein_rich": False, "dense": False},
    "Chana Masala & Tea": {"unit": "serving", "cal": 190.0, "p": 8.5, "c": 28.0, "f": 4.5, "fib": 5.5, "veg": True, "protein_rich": True, "dense": False},
    "Aloo Bonda & Tea": {"unit": "serving", "cal": 220.0, "p": 4.5, "c": 29.0, "f": 9.5, "fib": 2.2, "veg": True, "protein_rich": False, "dense": True},
    "Dal Vada & Tea": {"unit": "serving", "cal": 200.0, "p": 7.5, "c": 26.0, "f": 7.5, "fib": 4.0, "veg": True, "protein_rich": True, "dense": True},
    "Sunday": {"unit": "serving", "cal": 120.0, "p": 3.0, "c": 18.0, "f": 4.0, "fib": 1.5, "veg": True, "protein_rich": False, "dense": False},
    "Bombay Toast": {"unit": "pieces", "cal": 130.0, "p": 4.0, "c": 18.0, "f": 4.8, "fib": 1.2, "veg": True, "protein_rich": False, "dense": False},
    "Tea": {"unit": "ml", "cal": 45.0, "p": 1.5, "c": 7.5, "f": 1.2, "fib": 0.0, "veg": True, "protein_rich": False, "dense": False},

    # Desserts & Sweets
    "Kheer": {"unit": "g", "cal": 165.0, "p": 3.8, "c": 26.0, "f": 5.2, "fib": 0.4, "veg": True, "protein_rich": False, "dense": True},
    "Gajar Halwa / Kheer": {"unit": "g", "cal": 185.0, "p": 3.5, "c": 28.0, "f": 7.0, "fib": 1.2, "veg": True, "protein_rich": False, "dense": True},
    "Sabudana": {"unit": "g", "cal": 140.0, "p": 1.5, "c": 31.0, "f": 1.0, "fib": 0.5, "veg": True, "protein_rich": False, "dense": False},
    "Gulab Jamun": {"unit": "pieces", "cal": 150.0, "p": 2.5, "c": 24.0, "f": 5.5, "fib": 0.2, "veg": True, "protein_rich": False, "dense": True},
    "Gulab Jamun & Tea": {"unit": "serving", "cal": 190.0, "p": 3.8, "c": 31.0, "f": 6.5, "fib": 0.2, "veg": True, "protein_rich": False, "dense": True},
}

# OR MESS WEEKLY SCHEDULE (Agniveer -> Havildar)
OR_MESS_SCHEDULE = {
    "Monday": {
        "Breakfast": ["Rice", "Aloo Soyabeen / Aloo Rajma"],
        "Tea": ["Bread Pakoda & Tea"],
        "Lunch": ["Rice", "Chapati", "Mix Dal", "Mix Veg", "Seasonal Veg", "Kheer"],
        "Dinner": ["Rice", "Roti", "Dal", "Chicken Curry", "Mutter Paneer"]
    },
    "Tuesday": {
        "Breakfast": ["Namkeen Puri", "Kheer"],
        "Tea": ["Pakoda & Tea"],
        "Lunch": ["Rice", "Chapati", "Kadhi", "Mix Veg", "Salad"],
        "Dinner": ["Rice", "Chapati", "Dal", "Sahi Paneer"]
    },
    "Wednesday": {
        "Breakfast": ["Plain Paratha", "Dahi / Achar"],
        "Tea": ["Poha & Tea"],
        "Lunch": ["Rice", "Chapati", "Mix Dal", "Mix Veg", "Seasonal Veg", "Kheer"],
        "Dinner": ["Rice", "Chapati", "Dal", "Chicken Curry", "Mutter Paneer"]
    },
    "Thursday": {
        "Breakfast": ["Upma / Poha with Chutney", "Boiled Egg"],
        "Tea": ["Chana Masala & Tea"],
        "Lunch": ["Rice", "Chapati", "Kadhi", "Mix Veg", "Seasonal Veg"],
        "Dinner": ["Rice", "Chapati", "Dal", "Palak Paneer", "Egg Curry"]
    },
    "Friday": {
        "Breakfast": ["Puri & Sabji"],
        "Tea": ["Aloo Bonda & Tea"],
        "Lunch": ["Rice", "Chapati", "Mix Dal", "Mix Veg", "Seasonal Veg", "Kheer"],
        "Dinner": ["Rice", "Chapati", "Dal", "Chicken Curry", "Mutter Paneer"]
    },
    "Saturday": {
        "Breakfast": ["Khichdi", "Dahi / Achar"],
        "Tea": ["Dal Vada & Tea"],
        "Lunch": ["Rice", "Chapati", "Mix Dal", "Mix Veg", "Seasonal Veg"],
        "Dinner": ["Rice", "Chapati", "Dal", "Paneer Chilli", "Egg Curry"]
    },
    "Sunday": {
        "Breakfast": ["South Indian / Chinese / Pav Bhaji / Chhola Bhatura with Sweet"],
        "Tea": ["Sunday"],
        "Lunch": ["Biryani / Jeera Rice", "Shambhar / Sambar", "Chicken Curry", "Mutter Paneer", "Papad", "Salad", "Puri", "Kheer"],
        "Dinner": ["Rice", "Roti", "Dal", "Seasonal Veg"]
    }
}

# JCO MESS WEEKLY SCHEDULE (Naib Subedar -> Subedar Major)
JCO_MESS_SCHEDULE = {
    "Monday": {
        "Breakfast": ["Chapati", "Veg Curry", "Tea"],
        "Lunch": ["Lemon Rice", "Roti", "Dal Mix", "2 x Veg", "Mutter Paneer", "Salad", "Chutney"],
        "Dinner": ["Rice", "Roti", "Dal Mashri", "Chicken Curry", "01 x Veg", "01 x Normal Veg", "Gajar Halwa / Kheer"]
    },
    "Tuesday": {
        "Breakfast": ["Aloo Paratha / Paneer Paratha / Muli Paratha", "Chutney", "Tea"],
        "Lunch": ["Jeera Rice", "Roti", "Kadhi", "2 x Veg", "Papad", "Salad", "Karela Chips", "Mirchi Fry"],
        "Dinner": ["Rice", "Roti", "Dal Mung", "02 x Veg", "01 x Special Paneer", "Daliya Wheat"]
    },
    "Wednesday": {
        "Breakfast": ["Chola Bhatura", "Tea"],
        "Lunch": ["Rice Pulav", "Rumali Roti", "Dal Makhani", "2 x Veg", "Chutney", "Salad"],
        "Dinner": ["Rice", "Butter Roti", "Dal", "Chicken Curry", "Mutter Paneer", "02 x Veg", "Bombay Toast"]
    },
    "Thursday": {
        "Breakfast": ["Bread Omelet / Bread Cutlet", "Tea"],
        "Lunch": ["Veg Rice", "Roti", "Sambar", "02 x Veg", "Salad", "Papad", "Chutney"],
        "Dinner": ["Rice", "Roti", "Dal Mung", "Chicken Curry", "02 x Veg", "01 x Mutter Mushroom", "Kheer", "Sabudana"]
    },
    "Friday": {
        "Breakfast": ["Porota", "Chutney", "Egg Bhurji", "Tea"],
        "Lunch": ["Lemon Rice", "Roti", "Dal Rajmah", "2 x Veg", "Salad", "Mirchi Fry"],
        "Dinner": ["Rice", "Roti", "Dal Mix", "02 x Veg", "Chicken Egg Curry", "Gulab Jamun"]
    },
    "Saturday": {
        "Breakfast": ["Fried Rice", "Upma", "Boiled Egg", "Tea"],
        "Lunch": ["Jeera Rice", "Missi Roti", "Dal Arhar", "Mutter Paneer", "1 x Veg Normal", "Salad", "Chutney", "Mirchi Fry"],
        "Dinner": ["Rice", "Butter Roti", "Dal", "Chicken Curry", "Omelet", "02 x Veg", "01 x Veg Normal", "Jeera Rice"]
    },
    "Sunday": {
        "Breakfast": ["Idli, Dosa, Uthappam", "Sambar", "Chutney", "Gulab Jamun & Tea"],
        "Lunch": ["Chicken Biryani", "Veg Biryani", "Fish Curry", "Roti", "Papad", "Salad", "Kachumber", "Chutney"],
        "Dinner": ["Rice", "Rumali Roti", "Dal", "02 x Veg", "01 x Normal Veg", "Kheer"]
    }
}


def classify_mess_by_rank(rank_str):
    """
    Classifies a military personnel rank into 'OR' or 'JCO' mess category.
    
    OR Mess:
      Agniveer -> Havildar (including Sepoy, Naik, Havildar, CFN, Signal Man, CHM, CQMH, RHM, etc.)
    JCO Mess:
      Naib Subedar, Subedar, Subedar Major, and any equivalent JCO abbreviations/ranks.
      
    Args:
        rank_str (str): Raw rank string from database.
    Returns:
        dict: {
            'mess_type': 'OR' or 'JCO',
            'mess_label': 'OR MESS' or 'JCO MESS',
            'rank_clean': str,
            'is_jco': bool
        }
    """
    if not rank_str or not isinstance(rank_str, str):
        # Default fallback to OR Mess safely
        return {
            'mess_type': 'OR',
            'mess_label': 'OR MESS',
            'rank_clean': 'OR / Other Rank',
            'is_jco': False
        }

    raw = rank_str.strip()
    r_up = raw.upper()

    # JCO Rank patterns:
    # Subedar Major, Sub Maj, Sub Major, Subedar, Sub, Naib Subedar, Nb Sub, Nb Subedar, etc.
    # Be careful not to match substrings inside unrelated words
    jco_patterns = [
        r'\bSUBEDAR\s+MAJOR\b',
        r'\bSUB\s+MAJ\b',
        r'\bSUB\s+MAJOR\b',
        r'\bSUBEDAR\b',
        r'\bNAIB\s+SUBEDAR\b',
        r'\bNB\s+SUBEDAR\b',
        r'\bNB\s+SUB\b',
        r'\bNAIB\s+SUB\b',
        r'\bHONY\b',
        r'\bHONORARY\b',
        r'\bJCO\b'
    ]

    is_jco = False
    for pat in jco_patterns:
        if re.search(pat, r_up):
            is_jco = True
            break
            
    # Standalone 'SUB' without being part of another word
    if not is_jco and re.search(r'\bSUB\b', r_up):
        is_jco = True

    if is_jco:
        return {
            'mess_type': 'JCO',
            'mess_label': 'JCO MESS',
            'rank_clean': raw,
            'is_jco': True
        }
    else:
        return {
            'mess_type': 'OR',
            'mess_label': 'OR MESS',
            'rank_clean': raw,
            'is_jco': False
        }


def ensure_mess_menus_table():
    """
    Ensures that the `ai_mess_menus` table exists in the database
    and is seeded with the complete OR and JCO mess schedules.
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database to verify/seed ai_mess_menus table.")
        return False

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(CREATE_MESS_MENUS_TABLE_SQL)
        conn.commit()

        # Check if table already has entries
        cursor.execute("SELECT COUNT(*) AS cnt FROM ai_mess_menus")
        row = cursor.fetchone()
        count = row['cnt'] if row else 0

        if count == 0:
            logger.info("Seeding ai_mess_menus table with official OR and JCO menus...")
            insert_sql = """
                INSERT INTO ai_mess_menus (
                    mess_type, day_of_week, meal_type, food_item, default_serving_unit,
                    calories_per_100g, protein_per_100g, carb_per_100g, fat_per_100g, fiber_per_100g,
                    is_vegetarian, is_protein_rich, is_calorie_dense
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            insert_rows = []

            # 1. Seed OR Mess
            for day, meals in OR_MESS_SCHEDULE.items():
                for meal_type, items in meals.items():
                    for item_name in items:
                        info = NUTRITION_LOOKUP.get(item_name, {
                            "unit": "g", "cal": 100.0, "p": 4.0, "c": 15.0, "f": 3.0, "fib": 1.5,
                            "veg": True, "protein_rich": False, "dense": False
                        })
                        insert_rows.append((
                            'OR', day, meal_type, item_name, info['unit'],
                            info['cal'], info['p'], info['c'], info['f'], info['fib'],
                            info['veg'], info['protein_rich'], info['dense']
                        ))

            # 2. Seed JCO Mess
            for day, meals in JCO_MESS_SCHEDULE.items():
                for meal_type, items in meals.items():
                    for item_name in items:
                        info = NUTRITION_LOOKUP.get(item_name, {
                            "unit": "g", "cal": 100.0, "p": 4.0, "c": 15.0, "f": 3.0, "fib": 1.5,
                            "veg": True, "protein_rich": False, "dense": False
                        })
                        insert_rows.append((
                            'JCO', day, meal_type, item_name, info['unit'],
                            info['cal'], info['p'], info['c'], info['f'], info['fib'],
                            info['veg'], info['protein_rich'], info['dense']
                        ))

            cursor.executemany(insert_sql, insert_rows)
            conn.commit()
            logger.info(f"Successfully seeded {len(insert_rows)} mess menu records into ai_mess_menus.")

        return True
    except Error as e:
        logger.error(f"Error initializing/seeding ai_mess_menus table: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_mess_menu(mess_type, day_of_week=None):
    """
    Fetches the structured mess menu for a given mess type ('OR' or 'JCO')
    and day of the week ('Monday' ... 'Sunday').
    If day_of_week is None, returns the entire week's schedule.
    
    Returns:
        dict: { meal_type: [list of item dicts] }
    """
    ensure_mess_menus_table()

    conn = get_db_connection()
    if not conn:
        # Fallback to in-memory schedules if DB is temporarily unreachable
        source_schedule = OR_MESS_SCHEDULE if mess_type == 'OR' else JCO_MESS_SCHEDULE
        day_key = (day_of_week or "Monday").strip().capitalize()
        day_menu = source_schedule.get(day_key, source_schedule.get("Monday", {}))
        res = {}
        for m_type, items in day_menu.items():
            res[m_type] = []
            for it in items:
                n = NUTRITION_LOOKUP.get(it, {
                    "unit": "g", "cal": 100.0, "p": 4.0, "c": 15.0, "f": 3.0, "fib": 1.5,
                    "veg": True, "protein_rich": False, "dense": False
                })
                res[m_type].append({
                    'food_item': it,
                    'serving_unit': n['unit'],
                    'calories_per_100g': n['cal'],
                    'protein_per_100g': n['p'],
                    'carb_per_100g': n['c'],
                    'fat_per_100g': n['f'],
                    'fiber_per_100g': n['fib'],
                    'is_vegetarian': n['veg'],
                    'is_protein_rich': n['protein_rich'],
                    'is_calorie_dense': n['dense']
                })
        return res

    try:
        cursor = conn.cursor(dictionary=True)
        m_type = 'JCO' if str(mess_type).upper() == 'JCO' else 'OR'
        
        if day_of_week:
            clean_day = str(day_of_week).strip().capitalize()
            query = """
                SELECT meal_type, food_item, default_serving_unit,
                       calories_per_100g, protein_per_100g, carb_per_100g,
                       fat_per_100g, fiber_per_100g, is_vegetarian,
                       is_protein_rich, is_calorie_dense
                FROM ai_mess_menus
                WHERE mess_type = %s AND day_of_week = %s
                ORDER BY id ASC
            """
            cursor.execute(query, (m_type, clean_day))
        else:
            query = """
                SELECT day_of_week, meal_type, food_item, default_serving_unit,
                       calories_per_100g, protein_per_100g, carb_per_100g,
                       fat_per_100g, fiber_per_100g, is_vegetarian,
                       is_protein_rich, is_calorie_dense
                FROM ai_mess_menus
                WHERE mess_type = %s
                ORDER BY id ASC
            """
            cursor.execute(query, (m_type,))

        rows = cursor.fetchall()
        
        result = {}
        for r in rows:
            meal = r['meal_type']
            if meal not in result:
                result[meal] = []
            result[meal].append({
                'food_item': r['food_item'],
                'serving_unit': r['default_serving_unit'],
                'calories_per_100g': float(r['calories_per_100g'] or 0.0),
                'protein_per_100g': float(r['protein_per_100g'] or 0.0),
                'carb_per_100g': float(r['carb_per_100g'] or 0.0),
                'fat_per_100g': float(r['fat_per_100g'] or 0.0),
                'fiber_per_100g': float(r['fiber_per_100g'] or 0.0),
                'is_vegetarian': bool(r['is_vegetarian']),
                'is_protein_rich': bool(r['is_protein_rich']),
                'is_calorie_dense': bool(r['is_calorie_dense'])
            })
            
        return result
    except Error as e:
        logger.error(f"Error querying ai_mess_menus: {e}")
        return {}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
