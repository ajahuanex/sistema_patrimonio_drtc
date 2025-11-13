#!/bin/bash

################################################################################
# Environment Configuration Script for Production Deployment
# 
# This script generates and validates the .env.prod file with secure defaults
# and interactive prompts for required configuration values.
#
# Usage: ./scripts/configure-env.sh [OPTIONS]
#
# Options:
#   --domain DOMAIN          Set the domain name
#   --email EMAIL            Set the admin email
#   --interactive            Run in interactive mode (default)
#   --non-interactive        Skip interactive prompts (use defaults/args only)
#   --help                   Show this help message
#
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_EXAMPLE_FILE="$PROJECT_ROOT/.env.prod.example"
ENV_PROD_FILE="$PROJECT_ROOT/.env.prod"

# Default values
INTERACTIVE_MODE=true
DOMAIN=""
ADMIN_EMAIL=""

################################################################################
# Helper Functions
################################################################################

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

show_help() {
    cat << EOF
Environment Configuration Script for Production Deployment

Usage: ./scripts/configure-env.sh [OPTIONS]

Options:
  --domain DOMAIN          Set the domain name
  --email EMAIL            Set the admin email
  --interactive            Run in interactive mode (default)
  --non-interactive        Skip interactive prompts (use defaults/args only)
  --help                   Show this help message

Examples:
  # Interactive mode (default)
  ./scripts/configure-env.sh

  # Non-interactive with arguments
  ./scripts/configure-env.sh --domain example.com --email admin@example.com --non-interactive

EOF
    exit 0
}

################################################################################
# Validation Functions
################################################################################

validate_email() {
    local email="$1"
    local regex="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    if [[ $email =~ $regex ]]; then
        return 0
    else
        return 1
    fi
}

validate_domain() {
    local domain="$1"
    local regex="^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    
    if [[ $domain =~ $regex ]]; then
        return 0
    else
        return 1
    fi
}

validate_secret_key() {
    local key="$1"
    local min_length=50
    
    if [ ${#key} -ge $min_length ]; then
        return 0
    else
        print_error "SECRET_KEY must be at least $min_length characters"
        return 1
    fi
}

validate_password() {
    local password="$1"
    local min_length="$2"
    local name="$3"
    
    if [ ${#password} -lt $min_length ]; then
        print_error "$name must be at least $min_length characters"
        return 1
    fi
    
    # Check for complexity (at least one letter and one number)
    if [[ ! "$password" =~ [a-zA-Z] ]] || [[ ! "$password" =~ [0-9] ]]; then
        print_error "$name must contain at least one letter and one number"
        return 1
    fi
    
    return 0
}

validate_recaptcha_key() {
    local key="$1"
    local min_length=40
    
    if [ ${#key} -ge $min_length ]; then
        return 0
    else
        print_error "reCAPTCHA key must be at least $min_length characters"
        return 1
    fi
}

validate_security_code() {
    local code="$1"
    local min_length=16
    
    if [ ${#code} -lt $min_length ]; then
        print_error "Security code must be at least $min_length characters"
        return 1
    fi
    
    return 0
}

################################################################################
# Generation Functions
################################################################################

generate_secret_key() {
    # Generate a 64-character random string using alphanumeric and special chars
    local key=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)
    echo "$key"
}

generate_secure_password() {
    local length="$1"
    # Generate secure password with letters, numbers, and special characters
    local password=$(openssl rand -base64 $((length * 3 / 4)) | tr -d "=+/" | head -c $length)
    echo "$password"
}

################################################################################
# Interactive Prompts
################################################################################

prompt_domain() {
    while true; do
        read -p "Enter your domain name (e.g., patrimonio.example.com): " domain
        if validate_domain "$domain"; then
            DOMAIN="$domain"
            print_success "Domain validated: $DOMAIN"
            break
        else
            print_error "Invalid domain format. Please try again."
        fi
    done
}

prompt_email() {
    while true; do
        read -p "Enter admin email address: " email
        if validate_email "$email"; then
            ADMIN_EMAIL="$email"
            print_success "Email validated: $ADMIN_EMAIL"
            break
        else
            print_error "Invalid email format. Please try again."
        fi
    done
}

prompt_recaptcha_keys() {
    print_info "Get your reCAPTCHA keys from: https://www.google.com/recaptcha/admin"
    print_info "Use reCAPTCHA v2 'I'm not a robot' Checkbox"
    echo ""
    
    while true; do
        read -p "Enter reCAPTCHA Site Key (public key): " recaptcha_public
        if validate_recaptcha_key "$recaptcha_public"; then
            RECAPTCHA_PUBLIC_KEY="$recaptcha_public"
            break
        else
            print_error "Invalid reCAPTCHA public key. Must be at least 40 characters."
        fi
    done
    
    while true; do
        read -p "Enter reCAPTCHA Secret Key (private key): " recaptcha_private
        if validate_recaptcha_key "$recaptcha_private"; then
            RECAPTCHA_PRIVATE_KEY="$recaptcha_private"
            break
        else
            print_error "Invalid reCAPTCHA private key. Must be at least 40 characters."
        fi
    done
    
    print_success "reCAPTCHA keys configured"
}

prompt_email_config() {
    print_info "Configure email settings for notifications"
    echo ""
    
    read -p "Email SMTP host [smtp.gmail.com]: " email_host
    EMAIL_HOST="${email_host:-smtp.gmail.com}"
    
    read -p "Email SMTP port [587]: " email_port
    EMAIL_PORT="${email_port:-587}"
    
    while true; do
        read -p "Email username: " email_user
        if validate_email "$email_user"; then
            EMAIL_HOST_USER="$email_user"
            break
        else
            print_error "Invalid email format. Please try again."
        fi
    done
    
    read -sp "Email password (app password recommended): " email_pass
    echo ""
    EMAIL_HOST_PASSWORD="$email_pass"
    
    print_success "Email configuration completed"
}

################################################################################
# Main Configuration Function
################################################################################

configure_environment() {
    print_header "Production Environment Configuration"
    
    # Check if .env.prod.example exists
    if [ ! -f "$ENV_EXAMPLE_FILE" ]; then
        print_error ".env.prod.example not found at: $ENV_EXAMPLE_FILE"
        exit 1
    fi
    
    # Backup existing .env.prod if it exists
    if [ -f "$ENV_PROD_FILE" ]; then
        backup_file="${ENV_PROD_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        print_warning ".env.prod already exists. Creating backup: $backup_file"
        cp "$ENV_PROD_FILE" "$backup_file"
    fi
    
    # Interactive prompts if enabled
    if [ "$INTERACTIVE_MODE" = true ]; then
        print_info "Starting interactive configuration..."
        echo ""
        
        # Prompt for domain if not provided
        if [ -z "$DOMAIN" ]; then
            prompt_domain
        else
            if ! validate_domain "$DOMAIN"; then
                print_error "Invalid domain provided: $DOMAIN"
                exit 1
            fi
        fi
        
        # Prompt for email if not provided
        if [ -z "$ADMIN_EMAIL" ]; then
            prompt_email
        else
            if ! validate_email "$ADMIN_EMAIL"; then
                print_error "Invalid email provided: $ADMIN_EMAIL"
                exit 1
            fi
        fi
        
        # Prompt for reCAPTCHA keys
        prompt_recaptcha_keys
        
        # Prompt for email configuration
        prompt_email_config
    else
        # Non-interactive mode validation
        if [ -z "$DOMAIN" ] || [ -z "$ADMIN_EMAIL" ]; then
            print_error "Domain and email are required in non-interactive mode"
            exit 1
        fi
        
        if ! validate_domain "$DOMAIN"; then
            print_error "Invalid domain: $DOMAIN"
            exit 1
        fi
        
        if ! validate_email "$ADMIN_EMAIL"; then
            print_error "Invalid email: $ADMIN_EMAIL"
            exit 1
        fi
    fi
    
    print_header "Generating Secure Values"
    
    # Generate secure values
    print_info "Generating SECRET_KEY..."
    SECRET_KEY=$(generate_secret_key)
    validate_secret_key "$SECRET_KEY" || exit 1
    print_success "SECRET_KEY generated (${#SECRET_KEY} characters)"
    
    print_info "Generating POSTGRES_PASSWORD..."
    POSTGRES_PASSWORD=$(generate_secure_password 24)
    validate_password "$POSTGRES_PASSWORD" 20 "POSTGRES_PASSWORD" || exit 1
    print_success "POSTGRES_PASSWORD generated (${#POSTGRES_PASSWORD} characters)"
    
    print_info "Generating REDIS_PASSWORD..."
    REDIS_PASSWORD=$(generate_secure_password 20)
    validate_password "$REDIS_PASSWORD" 16 "REDIS_PASSWORD" || exit 1
    print_success "REDIS_PASSWORD generated (${#REDIS_PASSWORD} characters)"
    
    print_info "Generating PERMANENT_DELETE_CODE..."
    PERMANENT_DELETE_CODE=$(generate_secure_password 20)
    validate_security_code "$PERMANENT_DELETE_CODE" || exit 1
    print_success "PERMANENT_DELETE_CODE generated (${#PERMANENT_DELETE_CODE} characters)"
    
    print_header "Creating .env.prod File"
    
    # Copy example file and replace values
    cp "$ENV_EXAMPLE_FILE" "$ENV_PROD_FILE"
    
    # Replace generated values
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" "$ENV_PROD_FILE"
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" "$ENV_PROD_FILE"
    sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|g" "$ENV_PROD_FILE"
    sed -i "s|PERMANENT_DELETE_CODE=.*|PERMANENT_DELETE_CODE=$PERMANENT_DELETE_CODE|g" "$ENV_PROD_FILE"
    
    # Replace domain-related values
    sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost|g" "$ENV_PROD_FILE"
    sed -i "s|BASE_URL=.*|BASE_URL=https://$DOMAIN|g" "$ENV_PROD_FILE"
    sed -i "s|SSL_CERTIFICATE_PATH=.*|SSL_CERTIFICATE_PATH=/etc/letsencrypt/live/$DOMAIN/fullchain.pem|g" "$ENV_PROD_FILE"
    sed -i "s|SSL_CERTIFICATE_KEY_PATH=.*|SSL_CERTIFICATE_KEY_PATH=/etc/letsencrypt/live/$DOMAIN/privkey.pem|g" "$ENV_PROD_FILE"
    
    # Replace email values if in interactive mode
    if [ "$INTERACTIVE_MODE" = true ]; then
        sed -i "s|EMAIL_HOST=.*|EMAIL_HOST=$EMAIL_HOST|g" "$ENV_PROD_FILE"
        sed -i "s|EMAIL_PORT=.*|EMAIL_PORT=$EMAIL_PORT|g" "$ENV_PROD_FILE"
        sed -i "s|EMAIL_HOST_USER=.*|EMAIL_HOST_USER=$EMAIL_HOST_USER|g" "$ENV_PROD_FILE"
        sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD|g" "$ENV_PROD_FILE"
        sed -i "s|DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=Sistema Patrimonio <$EMAIL_HOST_USER>|g" "$ENV_PROD_FILE"
        
        sed -i "s|RECAPTCHA_PUBLIC_KEY=.*|RECAPTCHA_PUBLIC_KEY=$RECAPTCHA_PUBLIC_KEY|g" "$ENV_PROD_FILE"
        sed -i "s|RECAPTCHA_PRIVATE_KEY=.*|RECAPTCHA_PRIVATE_KEY=$RECAPTCHA_PRIVATE_KEY|g" "$ENV_PROD_FILE"
    fi
    
    print_success ".env.prod file created successfully"
    
    print_header "Configuration Summary"
    echo ""
    echo "Domain: $DOMAIN"
    echo "Admin Email: $ADMIN_EMAIL"
    echo "SECRET_KEY: [GENERATED - ${#SECRET_KEY} chars]"
    echo "POSTGRES_PASSWORD: [GENERATED - ${#POSTGRES_PASSWORD} chars]"
    echo "REDIS_PASSWORD: [GENERATED - ${#REDIS_PASSWORD} chars]"
    echo "PERMANENT_DELETE_CODE: [GENERATED - ${#PERMANENT_DELETE_CODE} chars]"
    
    if [ "$INTERACTIVE_MODE" = true ]; then
        echo "Email Host: $EMAIL_HOST"
        echo "Email User: $EMAIL_HOST_USER"
        echo "reCAPTCHA: [CONFIGURED]"
    fi
    
    echo ""
    print_warning "IMPORTANT: Keep these credentials secure!"
    print_warning "The .env.prod file contains sensitive information."
    echo ""
    
    # Validate final configuration
    print_header "Validating Configuration"
    validate_env_file
    
    print_success "Environment configuration completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Review the .env.prod file and adjust any additional settings"
    echo "  2. Run the deployment script: ./scripts/deploy-ubuntu.sh"
    echo ""
}

################################################################################
# Validation of Final .env.prod File
################################################################################

validate_env_file() {
    local errors=0
    
    print_info "Validating .env.prod file..."
    
    # Check if file exists
    if [ ! -f "$ENV_PROD_FILE" ]; then
        print_error ".env.prod file not found"
        return 1
    fi
    
    # Source the file to check variables
    set +u  # Temporarily disable undefined variable check
    source "$ENV_PROD_FILE"
    set -u
    
    # Validate critical variables
    if [ -z "${SECRET_KEY:-}" ] || [ "$SECRET_KEY" = "your-super-secret-key-here-change-this-in-production" ]; then
        print_error "SECRET_KEY is not configured"
        ((errors++))
    elif ! validate_secret_key "$SECRET_KEY"; then
        ((errors++))
    fi
    
    if [ -z "${POSTGRES_PASSWORD:-}" ] || [ "$POSTGRES_PASSWORD" = "your-secure-database-password-here" ]; then
        print_error "POSTGRES_PASSWORD is not configured"
        ((errors++))
    elif ! validate_password "$POSTGRES_PASSWORD" 20 "POSTGRES_PASSWORD"; then
        ((errors++))
    fi
    
    if [ -z "${REDIS_PASSWORD:-}" ] || [ "$REDIS_PASSWORD" = "your-secure-redis-password-here" ]; then
        print_error "REDIS_PASSWORD is not configured"
        ((errors++))
    elif ! validate_password "$REDIS_PASSWORD" 16 "REDIS_PASSWORD"; then
        ((errors++))
    fi
    
    if [ -z "${PERMANENT_DELETE_CODE:-}" ] || [ "$PERMANENT_DELETE_CODE" = "CHANGE-THIS-TO-SECURE-CODE-IN-PRODUCTION" ]; then
        print_error "PERMANENT_DELETE_CODE is not configured"
        ((errors++))
    elif ! validate_security_code "$PERMANENT_DELETE_CODE"; then
        ((errors++))
    fi
    
    if [ -z "${ALLOWED_HOSTS:-}" ] || [ "$ALLOWED_HOSTS" = "your-domain.com,www.your-domain.com,localhost" ]; then
        print_error "ALLOWED_HOSTS is not configured"
        ((errors++))
    fi
    
    if [ "${DEBUG:-}" != "False" ]; then
        print_error "DEBUG must be set to False in production"
        ((errors++))
    fi
    
    if [ "$errors" -eq 0 ]; then
        print_success "All critical variables validated successfully"
        return 0
    else
        print_error "Validation failed with $errors error(s)"
        return 1
    fi
}

################################################################################
# Parse Command Line Arguments
################################################################################

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                ADMIN_EMAIL="$2"
                shift 2
                ;;
            --interactive)
                INTERACTIVE_MODE=true
                shift
                ;;
            --non-interactive)
                INTERACTIVE_MODE=false
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

################################################################################
# Main Execution
################################################################################

main() {
    parse_arguments "$@"
    configure_environment
}

# Run main function
main "$@"
