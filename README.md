# Apple-Health-Data-Dashboard

## Overview
The Apple Health Data Dashboard is a web application built with Django that visualizes running and workout data from Apple Health. The dashboard provides insightful charts and metrics such as distance, pace, heart rate zones, cadence, and more. The application is designed for both individual users and demo purposes, allowing visitors to explore the functionality without logging in.

---

## Features
- Visualize running data: distance, pace, cadence, and heart rate.
- Heart rate zone calculations and time spent in Zone 2.
- Display of fastest and slowest workout times.
- Demo mode available for exploring features without an account.
- Clean and responsive dashboard interface.

---

## Requirements
- Python 3.10+
- Django 4.1+
- pip (Python package manager)
- Virtual environment tool (optional, recommended)

---

## Installation and Setup
### Clone the Repository
```bash
git clone https://github.com/thomasfonville/apple-health-data-dashboard.git
cd apple-health-data-dashboard
```

### Create and Activate a Virtual Environment (Recommended)
#### On macOS/Linux:
```bash
python3 -m venv env
source env/bin/activate
```

#### On Windows:
```bash
python -m venv env
env\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Generate a Secret Key
Every Django application requires a `SECRET_KEY`. Follow these steps to generate and set up your key:

1. Open a Python shell:
   ```bash
   python
   ```
2. Run the following code:
   ```python
   import secrets
   print(secrets.token_urlsafe(50))
   ```
   Copy the generated key.

3. Create a `.env` file in the project root:
   ```bash
   touch .env
   ```
4. Add the following to the `.env` file:
   ```
   SECRET_KEY=your-generated-secret-key
   ```

### Apply Database Migrations
```bash
python manage.py migrate
```

### Run the Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your web browser to view the application.

---

## Demo Mode
The application includes a demo mode for users who want to explore its features without creating an account.

- Demo user data is preloaded and accessible without authentication.
- To use demo mode, simply navigate to the dashboard without logging in.

---

## Usage
1. **Login or Explore in Demo Mode**
   - Registered users can log in to view their personalized dashboard.
   - Unauthenticated users will see demo data.

2. **Dashboard Features**
   - Interactive charts displaying distance, pace, cadence, and heart rate metrics.
   - Insights on heart rate zones, including Zone 2 percentage.
   - Detailed workout history and visualized workout routes.

---

## Adding Your Own Data
To use the dashboard with your own Apple Health data, you'll need to:

1. Export your Apple Health data to a `.zip` file via the Health app on your iPhone.
2. Parse the exported XML data into a format compatible with the application (this functionality can be added in future updates).
3. Import the processed data into the database.

---

## Contributing
Contributions are welcome! If you have suggestions or feature requests, feel free to open an issue or submit a pull request.

---

## Contact
For questions or support, reach out to:
- **Name:** Thomas Fonville
- **Email:** thomas@thomasfonville.com
- **GitHub:** [thomasfonville](https://github.com/thomasfonville)
