use crate::checks::oxy_test;
use anyhow::{Context, Result};
use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

#[derive(Debug, Serialize)]
pub struct FileScore {
    pub name: String,
    pub score: f32,
}

#[derive(Debug, Serialize)]
pub struct ScenarioResult {
    pub score: f32,
    pub file_scores: Vec<FileScore>,
}

/// Main entry point for the scenario subcommand.
///
/// Decision priority:
/// 1. --test-file given: run it directly
/// 2. --question + (--expected or --judge-criteria): write a temp test case and run it
/// 3. Neither: auto-discover *.test.yml files in --dir and run them all
/// 4. Nothing found: exit with a helpful error
pub fn run(
    dir: &Path,
    test_file: Option<&Path>,
    judge_criteria: Option<&str>,
    question: Option<&str>,
    expected: Option<&str>,
    judge_model: Option<&str>,
    runs: u8,
    verbose: bool,
    show_failures: bool,
) -> Result<ScenarioResult> {
    let db_url = std::env::var("OXY_DATABASE_URL").ok();

    // Priority 1: explicit test file
    if let Some(tf) = test_file {
        let score = oxy_test::check(dir, tf, db_url.as_deref(), verbose, show_failures)?;
        let name = tf.file_name().and_then(|n| n.to_str()).unwrap_or("test.yml").to_string();
        return Ok(ScenarioResult {
            score,
            file_scores: vec![FileScore { name, score }],
        });
    }

    // Priority 2: inline Q&A — judge_criteria and expected both map to the oxy test
    // `expected` field, which is always evaluated by the judge model.
    let assertion = judge_criteria.or(expected);
    if let (Some(q), Some(exp)) = (question, assertion) {
        let model = resolve_judge_model(dir, judge_model)?;
        let tf = write_judge_test(dir, q, exp, &model, runs)?;
        let check_result = oxy_test::check(dir, &tf, db_url.as_deref(), verbose, show_failures);
        fs::remove_file(&tf).ok();
        let score = check_result?;
        return Ok(ScenarioResult {
            score,
            file_scores: vec![FileScore { name: "(inline scenario test)".to_string(), score }],
        });
    }

    if judge_criteria.is_some() || expected.is_some() {
        anyhow::bail!("--judge-criteria / --expected require --question to also be provided");
    }
    if question.is_some() {
        anyhow::bail!("--question requires --expected or --judge-criteria to also be provided");
    }

    // Priority 3: auto-discovery
    let test_files = discover_tests(dir);
    if test_files.is_empty() {
        anyhow::bail!(
            "No .test.yml files found in {}.\n\
             Pass --test-file, or --question with --expected / --judge-criteria.",
            dir.display()
        );
    }

    let mut file_scores = Vec::new();
    for tf in &test_files {
        let score = oxy_test::check(dir, tf, db_url.as_deref(), verbose, show_failures)?;
        let name = tf.file_name().and_then(|n| n.to_str()).unwrap_or_default().to_string();
        file_scores.push(FileScore { name, score });
    }
    let avg = file_scores.iter().map(|f| f.score).sum::<f32>() / file_scores.len() as f32;

    Ok(ScenarioResult { score: avg, file_scores })
}

fn discover_tests(dir: &Path) -> Vec<PathBuf> {
    WalkDir::new(dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.file_type().is_file()
                && e.path()
                    .file_name()
                    .and_then(|n| n.to_str())
                    .map(|n| n.ends_with(".test.yml") && !n.starts_with('_'))
                    .unwrap_or(false)
        })
        .map(|e| e.path().to_owned())
        .collect()
}

fn find_agent_file(dir: &Path) -> Option<String> {
    WalkDir::new(dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .find(|e| {
            e.file_type().is_file()
                && e.path()
                    .file_name()
                    .and_then(|n| n.to_str())
                    .map(|n| n.ends_with(".agent.yml"))
                    .unwrap_or(false)
        })
        .and_then(|e| e.path().file_name().and_then(|n| n.to_str()).map(|s| s.to_string()))
}

/// Infer the judge model from config.yml, falling back to the --judge-model flag.
fn resolve_judge_model(dir: &Path, override_model: Option<&str>) -> Result<String> {
    if let Some(m) = override_model {
        return Ok(m.to_string());
    }
    let config_path = dir.join("config.yml");
    if !config_path.exists() {
        anyhow::bail!(
            "No config.yml found in {} — pass --judge-model explicitly.",
            dir.display()
        );
    }
    let contents = fs::read_to_string(&config_path)
        .with_context(|| format!("Could not read {}", config_path.display()))?;
    let config: serde_yaml::Value =
        serde_yaml::from_str(&contents).context("Could not parse config.yml")?;
    if let Some(models) = config.get("models").and_then(|v| v.as_sequence()) {
        for model in models {
            if let Some(name) = model.get("name").and_then(|v| v.as_str()) {
                return Ok(name.to_string());
            }
        }
    }
    anyhow::bail!("No named models in config.yml — pass --judge-model explicitly.")
}

/// Write a temporary .test.yml into dir, run oxy test on it, then delete it.
/// The `expected` field is evaluated by the judge model — it can be an exact answer
/// or a format/behavior description (e.g. "must be 2 significant figures").
fn write_judge_test(
    dir: &Path,
    question: &str,
    expected: &str,
    judge_model: &str,
    runs: u8,
) -> Result<PathBuf> {
    let agent_name = find_agent_file(dir)
        .context("No .agent.yml file found in --dir — cannot create a scenario test case")?;

    // Use Rust Debug formatting for strings: produces "quoted" YAML scalars with
    // proper escaping for any embedded special characters.
    let content = format!(
        "name: \"scenario-eval\"\ntarget: {agent_name}\n\nsettings:\n  runs: {runs}\n  concurrency: 1\n  judge_model: {judge_model}\n\ncases:\n  - prompt: {question:?}\n    expected: {expected:?}\n"
    );

    let path = dir.join("_scenario_eval.test.yml");
    fs::write(&path, content)
        .with_context(|| format!("Could not write temp test file at {}", path.display()))?;
    Ok(path)
}
