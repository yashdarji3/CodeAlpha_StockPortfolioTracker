# CodeAlpha_StockPortfolioTracker
# 📊 Stock Portfolio Tracker

A command-line Python application for tracking stock portfolios with real-time data from Yahoo Finance and Alpha Vantage.

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## ✨ Features

- **Secure Authentication**
  - User registration and login
  - Password hashing with bcrypt

- **Portfolio Management**
  - Add/update stock positions
  - Remove stocks or reduce positions
  - View detailed portfolio summaries

- **Data Integration**
  - Real-time data from Yahoo Finance
  - Alpha Vantage API support
  - Automatic MySQL database storage

- **Visualization**
  - Interactive portfolio pie charts
  - Performance tracking

## 🛠 Prerequisites

- Python 3.9+
- MySQL Server
- Alpha Vantage API key (free tier available)

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/HITMAN949/codealpha_tasks/tree/cd364f376b094e7fdaa7fc8dd88fd872ec196162/Simple%20Stock%20Porfolio%20Tracker
cd stock-portfolio-tracker
```
### 2. Set up virtual environment (recommended)
```bash
python -m venv venv
```
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
### 4. Configure environment
```ini
Create a .env file:
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_DATABASE=stock_portfolio_tracker
MYSQL_USER=portfolio_user
MYSQL_PASSWORD=your_secure_password
```
# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY=your_api_key_here
### 5. Set up MySQL database
```mysql
CREATE DATABASE stock_portfolio;
CREATE USER 'portfolio_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON stock_portfolio.* TO 'portfolio_user'@'localhost';
FLUSH PRIVILEGES;
```
### 6. Usage
```python
Run the application:
python tracker.py
```
