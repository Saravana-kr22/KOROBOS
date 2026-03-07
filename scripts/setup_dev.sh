# Add common local bin paths to PATH
export PATH="$HOME/.local/bin:$PATH"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Setting up CortexOS development environment..."

# 0. Check for Poetry
if ! command_exists poetry; then
    echo "Poetry not found! Attempting to install..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# 1. Install Backend Dependencies
echo "Installing backend dependencies..."
cd backend
poetry install
cd ..

# 2. Install Frontend Dependencies
echo "Installing frontend dependencies..."
if command_exists npm; then
    cd frontend
    npm install
    cd ..
else
    echo "Warning: npm not found. Frontend dependencies skipped."
fi

# 3. Setup Pre-commit Hooks
echo "Setting up pre-commit hooks..."
# Try to install pre-commit via pip if not found
if ! command_exists pre-commit; then
    pip install pre-commit --break-system-packages || pip install pre-commit
fi
pre-commit install

echo "Setup complete! Run 'make run' to start infrastructure, then 'make dev' to start services."
