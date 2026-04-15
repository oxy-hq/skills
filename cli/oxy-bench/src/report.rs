use crate::checks::{CheckResults, PassFail};
use crate::score::CompositeScore;
use crate::spec::Spec;

/// Print a human-readable evaluation report to stdout.
pub fn print(results: &CheckResults, composite: &CompositeScore, spec: &Spec) {
    println!("\n## Build Benchmark: {}", spec.name);
    println!("## Evaluation Level: {}", composite.level);

    println!("\n### Hard Checks");
    println!("{:<25} {}", "Check", "Result");
    println!("{}", "-".repeat(40));

    // File presence
    let counts: Vec<String> = results
        .file_presence
        .counts
        .iter()
        .map(|(t, n)| format!("{}:{}", t, n))
        .collect();
    let fp_label = if results.file_presence.pass { "✓" } else { "✗" };
    println!("{:<25} {} {}", "File presence", counts.join("  "), fp_label);

    // Validate
    println!("{:<25} {}", "oxy validate", pass_label(results.validate));

    // Build
    println!("{:<25} {}", "oxy build", pass_label(results.build));

    // Smoke
    match &results.smoke {
        Some(s) => println!(
            "{:<25} {}/{} ({:.0}%)",
            "Semantic smoke",
            s.passing,
            s.total,
            s.score * 100.0
        ),
        None => println!("{:<25} skipped (oxy build failed)", "Semantic smoke"),
    }

    println!("\n### Soft Checks");
    println!("{:<25} {}", "Check", "Result");
    println!("{}", "-".repeat(40));

    match results.oxy_test_score {
        Some(s) => println!("{:<25} {:.0}%", "Consistency score", s * 100.0),
        None => println!("{:<25} skipped (oxy build failed)", "Consistency score"),
    }

    if let Some(aq) = composite.ask_quality {
        println!("{:<25} {:.0}%", "Ask quality score", aq * 100.0);
    }

    println!("\n### Composite Score");
    println!(
        "  {:.0}%  (structural {:.0}%  smoke {:.0}%  consistency {:.0}%{})",
        composite.score * 100.0,
        composite.structural * 100.0,
        composite.smoke * 100.0,
        composite.consistency * 100.0,
        composite
            .ask_quality
            .map(|a| format!("  ask {:.0}%", a * 100.0))
            .unwrap_or_default()
    );
    println!();
}

fn pass_label(p: PassFail) -> &'static str {
    match p {
        PassFail::Pass => "PASS ✓",
        PassFail::Fail => "FAIL ✗",
        PassFail::Skipped => "SKIPPED",
    }
}
