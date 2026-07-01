#!/usr/bin/env python3
import os
import sys
import re

def main():
    print("=== Jules Auto-Configuration Utility ===")

    # 1. Detect repository info
    repo_root = os.getcwd()
    repo_name = os.path.basename(repo_root)
    print(f"Detected repository root: {repo_root}")
    print(f"Project name: {repo_name}")

    # 2. Analyze project stack
    has_bun = os.path.exists(os.path.join(repo_root, "bun.lock")) or os.path.exists(os.path.join(repo_root, "bun.lockb"))
    has_package_json = os.path.exists(os.path.join(repo_root, "package.json"))
    has_pyproject = os.path.exists(os.path.join(repo_root, "pyproject.toml"))
    has_requirements = os.path.exists(os.path.join(repo_root, "requirements.txt"))
    has_mise = os.path.exists(os.path.join(repo_root, "mise.toml"))

    # Database detection
    db_type = None  # 'postgres', 'mysql', 'sqlite', None
    db_name = repo_name.lower().replace("-", "_").replace(" ", "_")
    db_user = "tiller" if repo_name.lower() == "keepymoney" else db_name
    db_pass = db_user

    # Read package.json for dependencies and scripts
    scripts = {}
    if has_package_json:
        try:
            with open("package.json", "r") as f:
                content = f.read()
                if "postgres" in content or "pg" in content or "drizzle" in content:
                    db_type = "postgres"
                elif "mysql" in content or "sequelize" in content:
                    db_type = "mysql"
                elif "sqlite" in content:
                    db_type = "sqlite"
                
                # Simple extraction of scripts
                scripts_match = re.search(r'"scripts"\s*:\s*\{([^}]+)\}', content)
                if scripts_match:
                    for line in scripts_match.group(1).split(","):
                        m = re.search(r'"([^"]+)"\s*:\s*"([^"]+)"', line)
                        if m:
                            scripts[m.group(1)] = m.group(2)
        except Exception as e:
            print(f"Warning: Could not parse package.json: {e}")

    # Read compose files for services
    compose_files = ["compose.yml", "docker-compose.yml"]
    for cf in compose_files:
        if os.path.exists(cf):
            try:
                with open(cf, "r") as f:
                    content = f.read()
                    if "postgres" in content:
                        db_type = "postgres"
                    elif "mysql" in content or "mariadb" in content:
                        db_type = "mysql"
            except Exception:
                pass

    print(f"Stack analysis:")
    print(f"  Package Manager: {'Bun' if has_bun else 'npm' if has_package_json else 'Python' if (has_pyproject or has_requirements) else 'Unknown'}")
    print(f"  Database Detected: {db_type or 'None'}")
    print(f"  Mise integration: {'Yes' if has_mise else 'No'}")

    # 3. Create jules-setup.sh
    os.makedirs("scripts", exist_ok=True)
    setup_path = os.path.join("scripts", "jules-setup.sh")
    
    setup_lines = [
        "#!/bin/bash",
        "# Setup script for Google Jules cloud VM environment.",
        "# Generated automatically by jules-init.",
        "set -e",
        "",
        "echo \"=== Starting Jules Environment Setup ===\"",
        ""
    ]

    # Handle .env file setup
    setup_lines.append("# 1. Ensure correct .env is present")
    setup_lines.append("if [ ! -f .env ]; then")
    setup_lines.append("  if command -v op >/dev/null 2>&1 && op account list >/dev/null 2>&1; then")
    setup_lines.append("    echo \"1Password CLI detected and logged in. Injecting secrets...\"")
    if os.path.exists(".env.op"):
        setup_lines.append("    op inject -i .env.op > .env")
    else:
        setup_lines.append("    echo \"No .env.op file found. Using .env.example...\"")
        setup_lines.append("    cp .env.example .env 2>/dev/null || touch .env")
    setup_lines.append("  else")
    setup_lines.append("    echo \"1Password CLI not logged in or not present. Using .env.example...\"")
    if os.path.exists(".env.example"):
        setup_lines.append("    cp .env.example .env")
        if db_type == "postgres":
            # Map default docker port 5439 to native postgres port 5432
            setup_lines.append("    # Adjust DATABASE_URL to use the native Postgres port 5432 instead of docker 5439")
            setup_lines.append("    sed -i 's/:5439\\//:5432\\//g' .env 2>/dev/null || true")
    else:
        setup_lines.append("    touch .env")
    setup_lines.append("  fi")
    setup_lines.append("fi")
    setup_lines.append("")

    # Handle Database Service Setup
    if db_type == "postgres":
        setup_lines.extend([
            "# 2. Check if Postgres is installed and running",
            "if ! command -v psql >/dev/null 2>&1; then",
            "  echo \"PostgreSQL not found. Installing...\"",
            "  if command -v apt-get >/dev/null 2>&1; then",
            "    sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib",
            "  elif command -v brew >/dev/null 2>&1; then",
            "    brew install postgresql@17",
            "  fi",
            "fi",
            "",
            "echo \"Starting PostgreSQL service...\"",
            "if command -v systemctl >/dev/null 2>&1; then",
            "  sudo systemctl start postgresql || true",
            "elif command -v service >/dev/null 2>&1; then",
            "  sudo service postgresql start || true",
            "elif brew services list 2>&1 | grep -q postgresql; then",
            "  brew services start postgresql@17 || true",
            "fi",
            "",
            "# 3. Create the database and user",
            "echo \"Configuring database...\"",
            f"sudo -u postgres psql -c \"CREATE ROLE {db_user} WITH LOGIN PASSWORD '{db_pass}' SUPERUSER;\" || true",
            f"sudo -u postgres psql -c \"CREATE DATABASE {db_name} OWNER {db_user};\" || true",
            ""
        ])
    elif db_type == "mysql":
        setup_lines.extend([
            "# 2. Check if MySQL is installed and running",
            "if ! command -v mysql >/dev/null 2>&1; then",
            "  echo \"MySQL not found. Installing...\"",
            "  if command -v apt-get >/dev/null 2>&1; then",
            "    sudo apt-get update && sudo apt-get install -y mysql-server",
            "  fi",
            "fi",
            "",
            "echo \"Starting MySQL service...\"",
            "if command -v systemctl >/dev/null 2>&1; then",
            "  sudo systemctl start mysql || true",
            "elif command -v service >/dev/null 2>&1; then",
            "  sudo service mysql start || true",
            "fi",
            "",
            "# 3. Create the database and user",
            "echo \"Configuring database...\"",
            f"sudo mysql -e \"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}';\" || true",
            f"sudo mysql -e \"GRANT ALL PRIVILEGES ON *.* TO '{db_user}'@'localhost' WITH GRANT OPTION;\" || true",
            f"sudo mysql -e \"CREATE DATABASE IF NOT EXISTS {db_name};\" || true",
            ""
        ])

    # Handle Runtime Install & Dependencies
    setup_lines.append("# 4. Install project dependencies")
    if has_package_json:
        if has_bun:
            setup_lines.append("echo \"Installing Node dependencies with Bun...\"")
            setup_lines.append("bun install")
        else:
            setup_lines.append("echo \"Installing Node dependencies with npm...\"")
            setup_lines.append("npm install")
    elif has_pyproject or has_requirements:
        setup_lines.append("echo \"Installing Python dependencies...\"")
        if os.path.exists("poetry.lock"):
            setup_lines.append("poetry install")
        elif has_requirements:
            setup_lines.append("pip install -r requirements.txt")
    setup_lines.append("")

    # Handle Migrations and Seeding
    if db_type:
        setup_lines.append("# 5. Run migrations and seed database")
        if has_package_json:
            if "db:migrate" in scripts:
                cmd = "bun run db:migrate" if has_bun else "npm run db:migrate"
                setup_lines.append(f"echo \"Running migrations: {cmd}\"")
                setup_lines.append(cmd)
            elif "migrate" in scripts:
                cmd = "bun run migrate" if has_bun else "npm run migrate"
                setup_lines.append(f"echo \"Running migrations: {cmd}\"")
                setup_lines.append(cmd)
            elif os.path.exists("drizzle.config.ts") or os.path.exists("drizzle.config.js"):
                cmd = "bunx drizzle-kit migrate" if has_bun else "npx drizzle-kit migrate"
                setup_lines.append(f"echo \"Running drizzle migrations: {cmd}\"")
                setup_lines.append(cmd)
            elif os.path.exists("prisma/schema.prisma"):
                cmd = "bunx prisma db push" if has_bun else "npx prisma db push"
                setup_lines.append(f"echo \"Syncing prisma schema: {cmd}\"")
                setup_lines.append(cmd)

            if "db:seed" in scripts:
                cmd = "bun run db:seed" if has_bun else "npm run db:seed"
                setup_lines.append(f"echo \"Seeding database: {cmd}\"")
                setup_lines.append(cmd)
            elif "seed" in scripts:
                cmd = "bun run seed" if has_bun else "npm run seed"
                setup_lines.append(f"echo \"Seeding database: {cmd}\"")
                setup_lines.append(cmd)
        setup_lines.append("")

    # Handle Verification & Testing
    setup_lines.append("# 6. Run verification tests")
    if has_package_json:
        if "test" in scripts:
            cmd = "bun test" if has_bun else "npm test"
            setup_lines.append(f"echo \"Running verification tests: {cmd}\"")
            setup_lines.append(cmd)
    elif has_pyproject or has_requirements:
        setup_lines.append("echo \"Running verification tests with pytest...\"")
        setup_lines.append("pytest || python -m unittest")
    setup_lines.append("")

    setup_lines.append("echo \"=== Jules Environment Setup Completed Successfully! ===\"")

    # Write scripts/jules-setup.sh
    with open(setup_path, "w") as f:
        f.write("\n".join(setup_lines) + "\n")
    os.chmod(setup_path, 0o755)
    print(f"Created executable setup script at: {setup_path}")

    # 4. Patch mise.toml if it exists
    if has_mise:
        print("Mise config detected. Patching op inject hooks...")
        try:
            with open("mise.toml", "r") as f:
                content = f.read()
            
            # Look for enter hook with op inject
            target_re = r'"op inject -i \.env\.op > \.env"'
            replacement = '"if command -v op >/dev/null 2>&1 && op account list >/dev/null 2>&1; then op inject -i .env.op > .env; elif [ ! -f .env ]; then cp .env.example .env; fi"'
            
            if re.search(target_re, content):
                content = re.sub(target_re, replacement, content)
                with open("mise.toml", "w") as f:
                    f.write(content)
                print("  Successfully patched mise.toml with safe 1Password fallback hook.")
            else:
                print("  No vulnerable 1Password hook found in mise.toml.")
        except Exception as e:
            print(f"Warning: Could not patch mise.toml: {e}")

    # 5. Create or update AGENTS.md / GEMINI.md / CLAUDE.md
    agent_docs = ["AGENTS.md", "README.md"]
    doc_to_update = None
    for ad in agent_docs:
        if os.path.exists(ad):
            doc_to_update = ad
            break

    if not doc_to_update:
        doc_to_update = "AGENTS.md"
        print("Creating AGENTS.md...")

    jules_doc_section = f"""

## Jules Setup

Jules runs tasks in an isolated, cloud-based Linux VM. To configure Jules:
1. In the Jules UI / repository settings, configure the environment setup command:
   ```bash
   bash scripts/jules-setup.sh
   ```
2. This script automatically:
   - Sets up `.env` from `.env.example` (pointing `DATABASE_URL` to local Postgres on `5432`).
   - Starts a local Postgres service inside the VM (if applicable).
   - Bootstraps the database (if applicable).
   - Installs dependencies, runs migrations, seeds mock data, and runs unit tests.
"""

    try:
        if os.path.exists(doc_to_update):
            with open(doc_to_update, "r") as f:
                doc_content = f.read()
            if "Jules Setup" not in doc_content:
                with open(doc_to_update, "a") as f:
                    f.write(jules_doc_section)
                print(f"Appended Jules Setup documentation section to {doc_to_update}")
            else:
                print(f"Jules Setup documentation already exists in {doc_to_update}")
        else:
            with open(doc_to_update, "w") as f:
                f.write(f"# Project Guidelines\n{jules_doc_section}")
            print(f"Created {doc_to_update} with Jules Setup instructions.")
    except Exception as e:
        print(f"Warning: Could not update documentation: {e}")

    print("\n✅ Setup complete! Repository is optimized for Google Jules.")

if __name__ == "__main__":
    main()
