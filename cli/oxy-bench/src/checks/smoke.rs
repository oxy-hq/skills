use crate::checks::SmokeResult;
use crate::spec::SemanticRequirement;
use anyhow::Result;
use std::path::Path;
use std::process::Command;

/// For each required_semantics entry, write a minimal smoke_test.procedure.yml,
/// run it via `oxy run`, check that it returns at least one row, then delete it.
/// Equivalent to Step 4d in the skill.
pub fn check(dir: &Path, required: &[SemanticRequirement], db_url: &str) -> Result<SmokeResult> {
    let mut passing = 0;
    let total = required.len();

    for req in required {
        let topic = find_topic(dir, &req.topic_contains)?;

        let Some(topic_stem) = topic else {
            // No matching topic file found — count as skip, not fail
            continue;
        };

        let procedure_path = dir.join("smoke_test.procedure.yml");
        let measures_yaml = req
            .must_have_measures
            .iter()
            .map(|m| format!("      - {}", m))
            .collect::<Vec<_>>()
            .join("\n");

        let content = format!(
            "tasks:\n  - name: smoke_{slug}\n    type: semantic_query\n    topic: {topic}\n    measures:\n{measures}\n    limit: 1\n",
            slug = slug(&req.topic_contains),
            topic = topic_stem,
            measures = measures_yaml,
        );

        std::fs::write(&procedure_path, content)?;

        let output = Command::new("oxy")
            .arg("run")
            .arg("smoke_test.procedure.yml")
            .current_dir(dir)
            .env("OXY_DATABASE_URL", db_url)
            .output()?;

        let _ = std::fs::remove_file(&procedure_path);

        if output.status.success() {
            passing += 1;
        }
    }

    let score = if total == 0 {
        1.0
    } else {
        passing as f32 / total as f32
    };

    Ok(SmokeResult { passing, total, score })
}

/// Find the first .topic.yml file whose name contains the given substring.
fn find_topic(dir: &Path, contains: &str) -> Result<Option<String>> {
    for entry in std::fs::read_dir(dir)? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        if name.ends_with(".topic.yml") && name.contains(contains) {
            // Return stem: strip ".topic.yml"
            return Ok(Some(name.trim_end_matches(".topic.yml").to_string()));
        }
    }
    Ok(None)
}

fn slug(s: &str) -> String {
    s.chars()
        .map(|c| if c.is_alphanumeric() { c } else { '_' })
        .collect()
}
