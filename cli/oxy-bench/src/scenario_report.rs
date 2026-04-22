use crate::scenario::ScenarioResult;

pub fn print(result: &ScenarioResult) {
    println!("\n## Scenario Evaluation");

    if result.file_scores.len() > 1 {
        let width = result.file_scores.iter().map(|f| f.name.len()).max().unwrap_or(20).max(20);
        println!("\n{:<width$} {}", "Test file", "Score", width = width);
        println!("{}", "-".repeat(width + 8));
        for entry in &result.file_scores {
            println!("{:<width$} {:.0}%", entry.name, entry.score * 100.0, width = width);
        }
        println!("\nOverall: {:.0}%", result.score * 100.0);
    } else if let Some(entry) = result.file_scores.first() {
        println!("Test:  {}", entry.name);
        println!("Score: {:.0}%", result.score * 100.0);
    } else {
        println!("Score: {:.0}%", result.score * 100.0);
    }

    println!();
}
