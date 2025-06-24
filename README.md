# Augur 🔮

Augur is an AI-powered tool that automatically generates incident post-mortem reports from raw observability data.

## Features

- **Realistic Data Generation**: Creates comprehensive incident datasets with logs and metrics that simulate real-world scenarios
- **AI-Powered Analysis**: Uses LangChain and Google's Gemini Pro to analyze complex incident data
- **Structured Reports**: Generates detailed, professional post-mortem reports in Markdown format
- **CLI Interface**: Easy-to-use command-line interface built with Typer
- **Web Application**: Interactive Streamlit web app with curated demos and user upload functionality
- **Interactive Chat**: Ask follow-up questions about incidents using AI-powered chat
- **Demo Mode**: Complete end-to-end demo with sample incident data

## Technology Stack

- **Python 3.11+**
- **Streamlit**: Web application framework
- **LangChain**: AI framework for building LLM applications
- **Google Gemini Pro**: Advanced language model for analysis
- **Typer**: Modern CLI framework
- **python-dotenv**: Environment variable management

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd augur
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   - Get your Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Update the `.env` file with your API key:
     ```
     GOOGLE_API_KEY="your_actual_api_key_here"
     ```

## Usage

### Web Application (Recommended)

Run the Streamlit web application:

```bash
streamlit run app.py
```

This opens an interactive web interface with:
- **Curated Demos**: Explore pre-generated incident scenarios
- **Upload Your Data**: Analyze your own incident logs and metrics
- **Interactive Chat**: Ask questions about incidents
- **Real-time Analysis**: Get instant AI-powered insights

### Command Line Interface

#### Quick Demo

Run a complete demo to see Augur in action:

```bash
python -m src.main demo
```

This will:
1. Generate realistic incident data for a "bad deploy" scenario
2. Analyze the data using AI
3. Generate and display a post-mortem report
4. Save the report to `incidents/demo-incident/post_mortem_report.md`

#### Generate Incident Data

Create realistic incident data for testing or demonstration:

```bash
python -m src.main generate my-incident
```

This creates a directory structure at `incidents/my-incident/` with:
- **Logs**: JSON-formatted logs for auth-service, products-api, and checkout-service
- **Metrics**: CSV file with CPU, memory, and error rate data

#### Analyze Existing Incident Data

Analyze incident data and generate a post-mortem report:

```bash
python -m src.main analyze ./incidents/my-incident
```

This will:
1. Load all log and metrics files from the incident directory
2. Use AI to analyze the data
3. Generate a comprehensive post-mortem report
4. Display the report in the console
5. Save it as `post_mortem_report.md` in the incident directory

## Deployment

### Streamlit Community Cloud (Recommended)

Deploy your Streamlit app to Streamlit Community Cloud for easy, free hosting:

1. **Push to GitHub**: Ensure your code is in a GitHub repository
2. **Go to [share.streamlit.io](https://share.streamlit.io)**: Sign in with GitHub
3. **Create New App**:
   - Repository: Select your `augur` repository
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: Choose a custom subdomain (optional)
4. **Set Environment Variables**: In the app settings, add your Google API key:
   ```toml
   GOOGLE_API_KEY = "your_actual_api_key_here"
   ```
5. **Deploy**: Click "Deploy" and get your public HTTPS URL!

### Google Cloud Run

Deploy your Streamlit app to Google Cloud Run for scalable, production-ready hosting:

1. **Install Google Cloud SDK** and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and deploy**:
   ```bash
   # Build the container and push to Google Artifact Registry
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/augur
   
   # Deploy to Cloud Run
   gcloud run deploy augur \
     --image gcr.io/YOUR_PROJECT_ID/augur \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Set environment variables** (API keys):
   ```bash
   gcloud run services update augur --update-env-vars "GOOGLE_API_KEY=your-key-here"
   ```

4. **Access your app** at the provided HTTPS URL!

## Project Structure

```
/augur
├── /data_generator          # Incident data generation
│   ├── __init__.py
│   ├── main.py             # Data generator implementation
│   └── database_incident.py # Database incident generator
├── /incidents              # Generated incident data
│   ├── /bad_deploy/        # Memory leak scenario
│   ├── /database_overload/ # Database connection issues
│   └── /incident_example/  # Example incident directory
├── /src                    # Main application code
│   ├── __init__.py
│   ├── analyzer.py         # AI analyzer implementation
│   └── main.py            # CLI interface
├── app.py                  # Streamlit web application
├── Dockerfile             # Docker configuration for deployment
├── .env.example           # Environment variables template
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Incident Data Format

### Logs
Logs are stored as JSON lines files (`.log`) with the following structure:
```json
{
  "timestamp": "2024-01-15T14:05:00",
  "level": "ERROR",
  "service": "auth-service",
  "message": "Memory allocation failed",
  "memory_usage": 95,
  "cpu_usage": 90
}
```

### Metrics
Metrics are stored as CSV files with timestamped data:
```csv
timestamp,auth_service.cpu.utilization,auth_service.memory.usage,products_api.http.errors.5xx,checkout_service.http.errors.5xx
2024-01-15T14:05:00,85,90,25,30
```

## Generated Report Structure

The AI-generated post-mortem reports include:

1. **Summary**: Brief overview of the incident
2. **Timeline of Events**: Detailed, timestamped sequence of events
3. **Root Cause Analysis**: Technical explanation with supporting evidence
4. **Impact Analysis**: Assessment of affected services and business impact
5. **Action Items**: Recommended preventive measures

## Example Scenarios

The demo generates data for realistic incident scenarios:

### Bad Deploy Scenario
- **14:05**: Bad deploy to auth-service causes memory leak
- **14:05-14:45**: Auth service becomes unresponsive, causing downstream failures
- **14:45**: Deploy is rolled back, services recover
- **Impact**: Products API and checkout service experience high error rates

### Database Overload Scenario
- **16:30**: Database connection pool gets exhausted
- **16:30-17:15**: High latency and timeouts across multiple services
- **17:15**: Database issues resolved
- **Impact**: User, order, and payment services affected

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:
1. Check the existing issues
2. Create a new issue with detailed information
3. Include your Python version and error messages

---

**Note**: This tool is designed for educational and demonstration purposes. Always validate AI-generated reports against your actual incident data and team knowledge. 