"""Generate PgBouncer configuration file."""
import hashlib
import os
import re
from pathlib import Path
from typing import List, Tuple

# noinspection PyPackageRequirements
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


def load_env_for_userlist() -> List[Tuple[str, str]]:
    """Load the PGBOUNCER_USER environment variable and return a list
    containing a single tuple of the username and password.

    :return: A list containing a single tuple with the username and
        password.
    """
    pgbouncer_user = environ.Env().str("PGBOUNCER_USER")
    user, password = pgbouncer_user.split(":")

    # Generate the userlist.txt file
    user_password_pairs = [(user, password)]
    return user_password_pairs


def write_to_file(content: str, output_file_path: str) -> None:
    """Write the processed content to a new .ini file.

    :param content: Processed content with placeholders replaced by
        environment variable values.
    :param output_file_path: Path to the output .ini file.
    """
    with open(output_file_path, "w") as file:
        file.write(content)


def md5_hash_password(user: str, password: str) -> str:
    """Create an MD5 hash of the  username and password in the and then
    concatenated as required by PgBouncer.

    :param user: The database user's username.
    :param password: The database user's plain-text password.
    :return: The hashed password in the format 'md5<md5hash>'.
    """
    md5hash = hashlib.md5(user.encode() + password.encode()).hexdigest()  # nosec
    return f"md5{md5hash}"


def generate_userlist_file(user_password_pairs: List[Tuple[str, str]]) -> str:
    """Generate a userlist.txt file for PgBouncer with MD5 hashed passwords.

    :param user_password_pairs: A list of tuples containing username and
        password pairs.
    """
    content = ""
    for user, password in user_password_pairs:
        hashed_password = md5_hash_password(user, password)
        content += f'"{user}" "{hashed_password}"\n'

    return content


def main() -> None:
    """Generate PgBouncer configuration files (pgbouncer.ini and userlist.txt)
    based on environment variables and a sample INI file."""
    # Read environment variables from the .env file."""
    base_dir = Path(__file__).resolve().parent.parent
    environ.Env.read_env(os.path.join(base_dir, ".env"))

    # Load and process the .ini file
    ini_content = load_ini_with_env("pgbouncer_sample.ini")
    # Write the processed content to a new file
    write_to_file(ini_content, "pgbouncer.ini")

    # Generate the userlist.txt file
    content = generate_userlist_file(load_env_for_userlist())
    write_to_file(content, "userlist.txt")


if __name__ == "__main__":
    main()
