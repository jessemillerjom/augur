import typer
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import from data_generator
sys.path.append(str(Path(__file__).parent.parent))

from data_generator.main import generate_incident_data
from src.analyzer import IncidentAnalyzer

app = typer.Typer(
    name="augur",
    help="🔮 AI-powered incident post-mortem report generator",
    add_completion=False
)


@app.command()
def generate(
    incident_name: str = typer.Argument(..., help="Name of the incident to generate data for")
):
    """
    Generate realistic incident data for demo purposes.
    
    Creates a directory structure with logs and metrics that simulate
    a real incident scenario (bad deploy causing memory leak).
    """
    try:
        generate_incident_data(incident_name)
        typer.echo(f"✅ Successfully generated incident data for '{incident_name}'")
        typer.echo(f"📁 Data location: incidents/{incident_name}/")
    except Exception as e:
        typer.echo(f"❌ Error generating incident data: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def analyze(
    incident_path: str = typer.Argument(..., help="Path to the incident directory to analyze")
):
    """
    Analyze incident data and generate a post-mortem report.
    
    Uses AI to analyze logs and metrics, then generates a comprehensive
    post-mortem report in Markdown format.
    """
    try:
        # Validate incident path
        incident_path_obj = Path(incident_path)
        if not incident_path_obj.exists():
            typer.echo(f"❌ Incident path not found: {incident_path}", err=True)
            raise typer.Exit(1)
        
        typer.echo("🤖 Initializing AI analyzer...")
        analyzer = IncidentAnalyzer()
        
        typer.echo("📊 Loading incident data...")
        
        typer.echo("🧠 Generating post-mortem report...")
        report = analyzer.generate_report(incident_path)
        
        # Print the report to console
        typer.echo("\n" + "="*80)
        typer.echo("POST-MORTEM REPORT")
        typer.echo("="*80)
        typer.echo(report)
        typer.echo("="*80)
        
        # Save the report to file
        report_file = incident_path_obj / "post_mortem_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        typer.echo(f"💾 Report saved to: {report_file}")
        typer.echo("✅ Analysis complete!")
        
    except ValueError as e:
        typer.echo(f"❌ Configuration error: {str(e)}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error analyzing incident: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def demo():
    """
    Run a complete demo: generate incident data and analyze it.
    """
    try:
        incident_name = "demo-incident"
        
        typer.echo("🚀 Starting Augur demo...")
        
        # Generate incident data
        typer.echo("📝 Generating demo incident data...")
        generate_incident_data(incident_name)
        
        # Analyze the incident
        typer.echo("🔍 Analyzing the incident...")
        incident_path = f"incidents/{incident_name}"
        
        analyzer = IncidentAnalyzer()
        report = analyzer.generate_report(incident_path)
        
        # Print the report
        typer.echo("\n" + "="*80)
        typer.echo("DEMO POST-MORTEM REPORT")
        typer.echo("="*80)
        typer.echo(report)
        typer.echo("="*80)
        
        # Save the report
        report_file = Path(incident_path) / "post_mortem_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        typer.echo(f"💾 Report saved to: {report_file}")
        typer.echo("🎉 Demo completed successfully!")
        
    except Exception as e:
        typer.echo(f"❌ Demo failed: {str(e)}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 