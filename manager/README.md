# adms-manager

Multi-instance management tool for ADMS (Archival Document Management System).

## Installation

Copy the `manager/` directory to your server. The `adms-manager` script is a
POSIX shell script with no dependencies beyond Docker and Docker Compose.

```sh
chmod +x adms-manager
./adms-manager --help
```

## Quick Start

```sh
# Create a new instance
./adms-manager create my-archive

# Start it
./adms-manager start my-archive

# Check status
./adms-manager status my-archive

# Generate nginx config
./adms-manager proxy-config > /etc/nginx/sites-available/adms
```

## Commands

| Command | Description |
|---|---|
| `create [name]` | Interactive wizard to create a new instance |
| `list` | List all registered instances |
| `start <name>` | Start an instance |
| `stop <name>` | Stop an instance |
| `restart <name>` | Stop then start |
| `update <name>` | Pull latest images, migrate, restart |
| `backup <name>` | Create a backup archive |
| `restore <name> <file>` | Restore from backup |
| `logs <name> [service]` | Tail logs |
| `status <name>` | Show container status |
| `proxy-config` | Generate nginx server blocks |
| `destroy <name>` | Permanently remove an instance |
