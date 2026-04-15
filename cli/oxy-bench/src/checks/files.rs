use crate::checks::FilePresenceResult;
use crate::spec::ArtifactRequirement;
use anyhow::Result;
use std::path::Path;

/// Check that at least one file of each required artifact type exists in the directory.
/// Equivalent to Step 4a in the skill.
pub fn check(dir: &Path, required: &[ArtifactRequirement]) -> Result<FilePresenceResult> {
    let mut counts = Vec::new();
    let mut all_pass = true;

    for req in required {
        let extension = match req.artifact_type.as_str() {
            "topic" => "topic.yml",
            "agent" => "agent.yml",
            "view"  => "view.yml",
            other   => return Err(anyhow::anyhow!("Unknown artifact type: {}", other)),
        };

        let count = std::fs::read_dir(dir)?
            .filter_map(|e| e.ok())
            .filter(|e| {
                e.file_name()
                    .to_string_lossy()
                    .ends_with(extension)
            })
            .count();

        if count == 0 {
            all_pass = false;
        }

        counts.push((req.artifact_type.clone(), count));
    }

    Ok(FilePresenceResult { pass: all_pass, counts })
}
