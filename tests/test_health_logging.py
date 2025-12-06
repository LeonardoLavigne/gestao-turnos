from fastapi.testclient import TestClient
from app.main import app
import logging
import json

client = TestClient(app)

def test_health_check():
    """Verifica se o endpoint /health retorna 200 OK e JSON válido."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}

def test_logging_json(caplog):
    """Verifica se os logs estão sendo formatados como JSON."""
    with caplog.at_level(logging.INFO):
        logging.info("Teste de log JSON")
        pass
            
    # Teste manual do formatter
    from app.infrastructure.logger import JSONFormatter
    formatter = JSONFormatter()
    record = logging.LogRecord("test", logging.INFO, "path", 10, "Mensagem de teste", None, None)
    formatted = formatter.format(record)
    
    data = json.loads(formatted)
    assert data["message"] == "Mensagem de teste"
    assert "timestamp" in data
    assert data["level"] == "INFO"
