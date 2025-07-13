#!/bin/bash
set -euo pipefail

# PicoPixels LED Matrix Server Installation Script
# For Arch Linux with systemd

INSTALL_DIR="/opt/picopixels"
SERVICE_NAME="picopixels-server"
SERVICE_USER="picopixels"
VENV_DIR="$INSTALL_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_arch() {
    if ! command -v pacman &> /dev/null; then
        log_error "This script is designed for Arch Linux"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package database
    pacman -Sy --noconfirm
    
    # Install required packages
    pacman -S --needed --noconfirm python python-pip python-virtualenv
    
    log_success "System dependencies installed"
}

create_user() {
    # Create dialout group if it doesn't exist (Arch Linux doesn't have it by default)
    if ! getent group dialout &>/dev/null; then
        log_info "Creating dialout group..."
        groupadd dialout
        log_success "Dialout group created"
    fi
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        log_info "Creating service user: $SERVICE_USER"
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        usermod -a -G dialout "$SERVICE_USER"
        log_success "Service user created and added to dialout group"
    else
        log_info "Service user $SERVICE_USER already exists"
        # Ensure user is in dialout group
        usermod -a -G dialout "$SERVICE_USER"
    fi
}

setup_directories() {
    log_info "Setting up installation directory: $INSTALL_DIR"
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Set ownership
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    
    log_success "Installation directory created"
}

install_python_app() {
    log_info "Installing Python application..."
    
    # Copy server files
    cp "clients/web/server.py" "$INSTALL_DIR/"
    
    # Create virtual environment as the service user
    sudo -u "$SERVICE_USER" python -m venv "$VENV_DIR"
    
    # Install Python dependencies
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install flask pyserial
    
    # Set proper permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/server.py"
    
    log_success "Python application installed"
}

install_service() {
    log_info "Installing systemd service..."
    
    # Copy service file
    cp "picopixels-server.service" "/etc/systemd/system/"
    
    # Set proper permissions
    chmod 644 "/etc/systemd/system/picopixels-server.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    log_success "Systemd service installed"
}

create_update_script() {
    log_info "Creating update script..."
    
    cat > "/usr/local/bin/picopixels-update" << 'EOF'
#!/bin/bash
set -euo pipefail

# PicoPixels Update Script

INSTALL_DIR="/opt/picopixels"
SERVICE_NAME="picopixels-server"
SERVICE_USER="picopixels"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

if [[ ! -f "clients/web/server.py" ]]; then
    log_error "server.py not found. Run this script from the PicoPixels project directory."
    exit 1
fi

log_info "Stopping service..."
systemctl stop $SERVICE_NAME || true

log_info "Updating application..."
cp "clients/web/server.py" "$INSTALL_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/server.py"
chmod +x "$INSTALL_DIR/server.py"

log_info "Starting service..."
systemctl start $SERVICE_NAME

log_success "PicoPixels server updated successfully!"
systemctl status $SERVICE_NAME --no-pager
EOF

    chmod +x "/usr/local/bin/picopixels-update"
    
    log_success "Update script created at /usr/local/bin/picopixels-update"
}

enable_service() {
    log_info "Enabling and starting service..."
    
    # Enable service to start on boot
    systemctl enable "$SERVICE_NAME"
    
    # Start service
    systemctl start "$SERVICE_NAME"
    
    log_success "Service enabled and started"
}

show_status() {
    log_info "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager || true
    
    echo
    log_info "Service logs (last 10 lines):"
    journalctl -u "$SERVICE_NAME" -n 10 --no-pager || true
    
    echo
    log_success "Installation completed!"
    echo
    echo "Service management commands:"
    echo "  Start:   sudo systemctl start $SERVICE_NAME"
    echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
    echo "  Restart: sudo systemctl restart $SERVICE_NAME"
    echo "  Status:  sudo systemctl status $SERVICE_NAME"
    echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
    echo
    echo "Update command:"
    echo "  sudo picopixels-update"
    echo
    echo "Web interface should be available at:"
    echo "  http://localhost:5000"
    echo "  http://$(hostname -I | awk '{print $1}'):5000"
}

main() {
    echo "========================================"
    echo "  PicoPixels Server Installation"
    echo "========================================"
    echo
    
    check_root
    check_arch
    
    # Check if we're in the right directory
    if [[ ! -f "clients/web/server.py" ]]; then
        log_error "server.py not found. Please run this script from the PicoPixels project directory."
        exit 1
    fi
    
    install_dependencies
    create_user
    setup_directories
    install_python_app
    install_service
    create_update_script
    enable_service
    show_status
}

main "$@"