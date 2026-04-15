use crate::checks::PassFail;
use anyhow::Result;
use std::path::Path;
use std::process::Command;

/// Run `oxy validate` in the builder directory.
/// Equivalent to Step 4b in the skill.
pub fn check(dir: &Path) -> Result<PassFail> {
    let output = Command::new("oxy")
        .arg("validate")
        .current_dir(dir)
        .output()?;

    if output.status.success() {
        Ok(PassFail::Pass)
    } else {
        Ok(PassFail::Fail)
    }
}
