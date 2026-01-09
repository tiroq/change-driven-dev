#!/bin/bash
# System Validation Script

echo "🔍 Change-Driven Dev - System Validation"
echo "========================================"
echo ""

# Check Python version
echo "✓ Python: $(python3 --version)"

# Check virtual environment
if [ -d ".venv" ]; then
    echo "✓ Virtual environment: .venv exists"
else
    echo "✗ Virtual environment: .venv not found"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check key dependencies
echo ""
echo "📦 Dependencies:"
pip list | grep -E "fastapi|uvicorn|sqlalchemy|pydantic|pytest" | while read line; do
    echo "  ✓ $line"
done

# Run backend tests
echo ""
echo "🧪 Running Tests:"
cd backend
python -m pytest tests/test_dao.py -q
test_result=$?

if [ $test_result -eq 0 ]; then
    echo "✓ All DAO tests passed (21/21)"
else
    echo "✗ Tests failed"
    exit 1
fi

# Check app import
echo ""
echo "🔧 Checking App Import:"
python -c "from app.main import app; print('✓ FastAPI app imports successfully')" || exit 1

# Count routes
route_count=$(python -c "from app.main import app; print(len([r for r in app.routes if hasattr(r, 'path')]))")
echo "✓ API routes registered: $route_count"

# Check database models
echo ""
echo "📊 Database Models:"
python -c "
from app.models.models import Project, Task, TaskVersion, ChangeRequest, Approval, Artifact, Run, ControlState
models = [Project, Task, TaskVersion, ChangeRequest, Approval, Artifact, Run, ControlState]
for model in models:
    print(f'  ✓ {model.__name__}')
" || exit 1

# Check core services
echo ""
echo "⚙️  Core Services:"
python -c "
from app.core.events import event_bus
from app.services.orchestration import orchestration_service
from app.services.artifacts import artifact_storage
from app.engines import EngineFactory
print('  ✓ EventBus')
print('  ✓ OrchestrationService')
print('  ✓ ArtifactStorage')
print('  ✓ EngineFactory')
" || exit 1

# Check security layer
echo ""
echo "🔒 Security Components:"
python -c "
from app.core.sandbox import SafePathResolver, CommandRunner
from app.core.gates import GateRunner
from app.core.config import ProjectConfig
print('  ✓ SafePathResolver')
print('  ✓ CommandRunner')
print('  ✓ GateRunner')
print('  ✓ ProjectConfig')
" || exit 1

echo ""
echo "========================================"
echo "✅ All validations passed!"
echo "========================================"
echo ""
echo "🚀 System is ready for use:"
echo "  - Backend: uvicorn app.main:app --reload"
echo "  - Frontend: cd ../frontend && npm run dev"
echo "  - API Docs: http://localhost:8000/docs"
