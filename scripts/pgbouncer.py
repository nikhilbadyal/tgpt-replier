"""Generate PgBouncer configuration file."""

import os
import re
from pathlib import Path

import environ


def load_ini_with_env(file_path: str) -> str:
    """Load the INI file and replace placeholders with the corresponding
    environment variable values.

    :param file_path: Path to the .ini file containing placeholders.
    :return: Content of the .ini file with placeholders replaced by
             environment variable values.
    """
    with open(file_path, "r") as file:
        content = file.read()

    updated_content: str = re.sub(
        r"%env\((.*?)\)%", lambda match: environ.Env().str(match.group(1)), content  # type: ignore
    )

    return updated_content


def write_ini_to_file(content: str, output_file_path: str) -> None:
    """Write the processed content to a new .ini file.

    :param content: Processed content with placeholders replaced by environment variable values.
    :param output_file_path: Path to the output .ini file.
    """
    with open(output_file_path, "w") as file:
        file.write(content)


def main() -> None:
    """Read environment variables from the .env file."""
    base_dir = Path(__file__).resolve().parent.parent
    environ.Env.read_env(os.path.join(base_dir, ".env"))

    # Load and process the .ini file
    ini_content = load_ini_with_env("pgbouncer_sample.ini")

    # Write the processed content to a new file
    write_ini_to_file(ini_content, "pgbouncer.ini")


if __name__ == "__main__":
    main()
