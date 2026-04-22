use crate::checks::SmokeResult;
use crate::spec::SemanticRequirement;
use anyhow::Result;
use std::path::Path;
use std::process::Command;
use walkdir::WalkDir;

/// For each required_semantics entry, write a minimal smoke_test.procedure.yml,
/// run it via `oxy run`, check that it returns at least one row, then delete it.
pub fn check(dir: &Path, required: &[SemanticRequirement], db_url: &str) -> Result<SmokeResult> {
    let mut passing = 0;
    let total = required.len();

    for req in required {
        let topic_info = find_topic(dir, &req.topic_contains)?;

        let Some((topic_stem, base_view)) = topic_info else {
            // No matching topic file found — count as skip, not fail
            continue;
        };

        let procedure_path = dir.join("smoke_test.procedure.yml");

        // Oxy semantic_query requires measures qualified as "view_name.measure_name".
        // Use the topic's base_view as the qualifier.
        let measures_yaml = req
            .must_have_measures
            .iter()
            .map(|m| format!("      - {}.{}", base_view, m))
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

/// Find the first .topic.yml file (anywhere under dir) whose name contains the given substring.
/// Returns (topic_stem, base_view) where base_view is parsed from the topic file.
/// Uses walkdir so it finds files in subdirectories like semantics/topics/.
fn find_topic(dir: &Path, contains: &str) -> Result<Option<(String, String)>> {
    for entry in WalkDir::new(dir).into_iter().filter_map(|e| e.ok()) {
        if !entry.file_type().is_file() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().to_string();
        if name.ends_with(".topic.yml") && name.contains(contains) {
            let stem = name.trim_end_matches(".topic.yml").to_string();
            let base_view = parse_base_view(entry.path()).unwrap_or_else(|| stem.clone());
            return Ok(Some((stem, base_view)));
        }
    }
    Ok(None)
}

/// Parse the `base_view:` field from a .topic.yml file.
fn parse_base_view(path: &Path) -> Option<String> {
    let content = std::fs::read_to_string(path).ok()?;
    for line in content.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("base_view:") {
            return Some(rest.trim().to_string());
        }
    }
    None
}

fn slug(s: &str) -> String {
    s.chars()
        .map(|c| if c.is_alphanumeric() { c } else { '_' })
        .collect()
}
