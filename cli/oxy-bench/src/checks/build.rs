use crate::checks::PassFail;
use anyhow::Result;
use std::path::Path;
use std::process::Command;

/// Run `oxy build` in the builder directory.
/// Equivalent to Step 4c in the skill.
pub fn check(dir: &Path, db_url: &str) -> Result<PassFail> {
    let output = Command::new("oxy")
        .arg("build")
        .current_dir(dir)
        .env("OXY_DATABASE_URL", db_url)
        .output()?;

    if output.status.success() {
        Ok(PassFail::Pass)
    } else {
        Ok(PassFail::Fail)
    }
}
