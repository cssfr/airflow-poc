# Airflow POC

A Proof of Concept project using Apache Airflow for workflow orchestration and data pipeline management.

## Overview

This project demonstrates the setup and usage of Apache Airflow for creating, scheduling, and monitoring data workflows.

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized setup)
- Git

## Installation

### Local Development Setup

1. Clone the repository:
```bash
git clone <your-github-repo-url>
cd airflow-poc
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize Airflow database:
```bash
airflow db init
```

5. Create an admin user:
```bash
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

6. Start the Airflow webserver:
```bash
airflow webserver --port 8080
```

7. In a new terminal, start the scheduler:
```bash
airflow scheduler
```

## Project Structure

```
airflow-poc/
├── dags/                   # Airflow DAGs
├── plugins/               # Custom Airflow plugins
├── logs/                  # Airflow logs
├── config/                # Configuration files
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker setup (optional)
└── README.md             # This file
```

## Usage

1. Access the Airflow web interface at `http://localhost:8080`
2. Login with the admin credentials you created
3. Browse and manage your DAGs from the web interface

## Development

### Adding New DAGs

1. Create your DAG file in the `dags/` directory
2. Follow Airflow best practices for DAG structure
3. Test your DAG locally before deploying

### Configuration

- Airflow configuration can be found in `config/airflow.cfg`
- Environment variables can be set in `.env` file

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Airflow Tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)
