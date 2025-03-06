# Lezo LGU System

![Lezo LGU System](https://img.shields.io/badge/Django-5.0-green.svg) ![License](https://img.shields.io/badge/License-MIT-blue.svg)

A Django-based web application for managing population and services in Lezo, Aklan. Developed by Ernan T. Baldomero. Visit [ernan.net](https://ernan.net) for more information about the developer.

## Overview

The **Lezo LGU System** is a lightweight, feature-rich, and scalable web application designed to run on Ubuntu 24.04 LTS within a VMware virtual machine (1 vCPU, 1GB RAM, 20GB SSD). It provides an intuitive interface for managing citizen data, services, and relationships, accessible at `http://192.168.65.131:8000`. Key features include Excel-based data imports, genealogy inference, AJAX-driven interactions, and a novice-friendly setup process.

## Features

- **Web Interface:** Welcome page with navigation. Setup page to upload `voters.xlsx` or initialize an empty database. Citizens page with search, pagination, and dynamic service/relationship management.
- **Data Import:** Import citizen data from a 12-tab Excel file via command line or web upload.
- **Genealogy Inference:** Supports direct (e.g., "brother") and inferred (e.g., "uncle") relationships.
- **Database:** PostgreSQL for runtime, SQLite for testing.
- **Ease of Use:** Single-script installation, GUI launcher, and detailed logging.

## Requirements

- **OS:** Ubuntu 24.04 LTS
- **VM Specs:** VMware VM with 1 vCPU, 1GB RAM, 20GB SSD
- **Network:** Bridged network, accessible at `192.168.65.131:8000`
- **Dependencies:** Listed in `requirements.txt`

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/ernantbaldomero/lezo-system.git
   cd lezo-system
   
2. **Run the Installation Script:**
   ```bash
   chmod +x install.sh
   ./install.sh


This script:
- **Installs Python 3, pip, virtualenv, PostgreSQL, and Gunicorn.
- **Sets up the PostgreSQL database (lezo_db, user: lezo_user, password: Lezo2025).
- **Creates and activates a virtual environment.
- **Installs Python dependencies from requirements.txt.
- **Applies database migrations and runs tests.
- **Configures environment variables in .env.

## Running the Application
```markdown
1. **Start the Server:**
   ```bash
   ./start.sh
   
OR double-click lezo-system.desktop in a GUI environment to launch with a terminal.

2. **Access the Application:**
Open your browser and navigate to http://192.168.65.131:8000/.

## Web Interface

- **Welcome Page (`/`):** Links to Setup and Citizens pages.
- **Setup Page (`/setup`):** Upload a 12-tab `voters.xlsx` file (sheets: Agcawilan, Bagto, Bugasongan, Carugdog, Cogon, Ibao, Mina, Poblacion, Silakat Nonok, Sta. Cruz, Sta. Cruz Biga-a, Tayhawan) or initialize an empty database.
- **Citizens Page (`/citizens`):** Lists citizens with name, barangay, services, and relationships. Search by name (case-insensitive). Pagination (10 per page). Add services (e.g., "AICS") or relationships (e.g., "brother") via AJAX buttons.

## Command Line Import
To import data manually:
```bash
python manage.py import_voters /path/to/voters.xlsx

## Project Structure
```markdown

lezo-system/
├── lezo_lgu/         # Django project directory
├── core/            # Main Django app
├── install.sh       # Installation script
├── start.sh         # Startup script
├── requirements.txt # Python dependencies
├── lezo-system.desktop # Desktop launcher
├── README.md        # This file
├── LICENSE.txt      # MIT License
├── .env            # Environment variables (generated)
└── app.log         # Runtime logs

## Troubleshooting

- **Logs:** Check `app.log` for detailed error messages.
- **Network Issues:** Ensure the VM uses a bridged network and the IP matches `192.168.65.131`.
- **Permissions:** Run `chmod +x start.sh` if the startup script fails.

## Contributing

Feel free to fork this repository, submit issues, or create pull requests. Contributions are welcome to enhance features like reporting or authentication.

## License

This project is licensed under the MIT License. See [LICENSE.txt](LICENSE.txt) for details. © 2025 Ernan T. Baldomero. All rights reserved.

## Contact

For support or inquiries, visit [ernan.net](https://ernan.net) or open an issue on this repository.






