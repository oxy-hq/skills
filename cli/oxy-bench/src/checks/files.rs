use crate::checks::FilePresenceResult;
use crate::spec::ArtifactRequirement;
use anyhow::Result;
use std::path::Path;
use walkdir::WalkDir;

/// Check that at least one file of each required artifact type exists in the directory.
/// Searches recursively so files in subdirectories (e.g. semantics/views/) are found.
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

        let count = WalkDir::new(dir)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
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
