from pathlib import Path

import click
import python_terraform as pt

from one_click import utils


BACKEND_DIR = Path.cwd()
BASE_DIR = Path(__file__).parent
TERRAFORM_DIR = str(BASE_DIR / "terraform")


@click.group()
def main():
    pass


@main.command()
@click.option("--public_key_path", default="~/.ssh/id_rsa.pub")
@click.option("--private_key_path", default="~/.ssh/id_rsa")
@click.option(
    "--py",
    default="3.7",
    help='Python version. Options are 3.7, 3.6, 3.5, 2.7.',
)
@click.argument("git_path")
def deploy(git_path, public_key_path=None, private_key_path=None, py=None):
    image_version = utils.py_version_to_image(py)
    var = {
        "base_directory": str(BASE_DIR),
        "path_to_public_key": public_key_path,
        "path_to_private_key": private_key_path,
        "github_clone_link": git_path,
        "image_version": image_version,
    }

    tf = pt.Terraform()
    tf.init(
        dir_or_plan=str(BACKEND_DIR),
        from_module=TERRAFORM_DIR,
        capture_output=False,
    )
    return_code, _, _ = tf.apply(var=var, capture_output=False)

    if not return_code:
        tfvars = utils.dict_to_tfvars(var)
        with open(BACKEND_DIR / "terraform.tfvars", "w") as f:
            f.write(tfvars)


@main.command()
def destroy():
    required_state_files = (
        ".terraform",
        "main.tf",
        "terraform.tfstate",
        "terraform.tfvars",
    )
    has_all_required_files = all(
        map(lambda path: any(BACKEND_DIR.glob(path)), required_state_files)
    )
    if not has_all_required_files:
        raise click.UsageError(
            f"""
            Deployment directory is missing some or all of the required state
            files: {required_state_files}. Make sure that you actually have a
            project deployed and that you are in its correct directory."""
        )

    tf = pt.Terraform()
    tf.destroy(capture_output=False)
