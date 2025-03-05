use anyhow::{Context, Result};
use byteorder::{LittleEndian, ReadBytesExt};
use indicatif::{ProgressBar, ProgressStyle};
use regex::Regex;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{self, BufReader, Cursor, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use walkdir::WalkDir;

// Error type definitions
#[derive(thiserror::Error, Debug)]
enum TermiusToolError {
    #[error("File not found: {0}")]
    FileNotFound(String),
    
    #[error("Failed to extract ASAR file: {0}")]
    AsarExtractFailed(String),
    
    #[error("Failed to modify file: {0}")]
    FileModificationFailed(String),
    
    #[error("ASAR file format error: {0}")]
    AsarFormatError(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] io::Error),
    
    #[error("JSON error: {0}")]
    JsonError(#[from] serde_json::Error),
}

// ASAR file processing structure
struct AsarFile {
    header: Value,
    header_size: u32,
    files: HashMap<String, Vec<u8>>,
}

impl AsarFile {
    // Load ASAR from file
    fn from_file(path: &Path) -> Result<Self> {
        let file = File::open(path)?;
        let mut reader = BufReader::new(file);
        
        // Read header size
        let header_size = reader.read_u32::<LittleEndian>()?;
        
        // Read header JSON
        let mut header_data = vec![0; header_size as usize];
        reader.read_exact(&mut header_data)?;
        
        let header: Value = serde_json::from_slice(&header_data)?;
        
        // Initialize file collection
        let mut files = HashMap::new();
        
        // Read all files
        Self::extract_files(&header["files"], "", &mut reader, header_size + 8, &mut files)?;
        
        Ok(Self {
            header,
            header_size,
            files,
        })
    }
    
    // Recursively extract files
    fn extract_files(
        node: &Value, 
        path: &str, 
        reader: &mut BufReader<File>, 
        base_offset: u32,
        files: &mut HashMap<String, Vec<u8>>
    ) -> Result<()> {
        if let Some(obj) = node.as_object() {
            for (name, info) in obj {
                let file_path = if path.is_empty() {
                    name.clone()
                } else {
                    format!("{}/{}", path, name)
                };
                
                if info["files"].is_object() {
                    // This is a directory
                    Self::extract_files(&info["files"], &file_path, reader, base_offset, files)?;
                } else if let (Some(size), Some(offset)) = (
                    info["size"].as_u64(),
                    info["offset"].as_u64()
                ) {
                    // This is a file
                    let size = size as usize;
                    let offset = offset as u64 + base_offset as u64;
                    
                    // Read file content
                    reader.seek(SeekFrom::Start(offset))?;
                    let mut content = vec![0; size];
                    reader.read_exact(&mut content)?;
                    
                    // Store file content
                    files.insert(file_path, content);
                }
            }
        }
        
        Ok(())
    }
    
    // Extract to directory
    fn extract_to_dir(&self, output_dir: &Path) -> Result<()> {
        fs::create_dir_all(output_dir)?;
        
        let pb = ProgressBar::new(self.files.len() as u64);
        pb.set_style(ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:50.cyan/blue}] {pos}/{len} ({eta})")
            .unwrap()
            .progress_chars("#>-"));
        
        for (path, content) in &self.files {
            let full_path = output_dir.join(path);
            
            // Create parent directory
            if let Some(parent) = full_path.parent() {
                fs::create_dir_all(parent)?;
            }
            
            // Write file
            let mut file = File::create(&full_path)?;
            file.write_all(content)?;
            
            pb.inc(1);
        }
        
        pb.finish_with_message("Extraction complete");
        Ok(())
    }
}

// Close Termius process
fn kill_termius() -> Result<()> {
    println!("Checking Termius process...");
    let _ = Command::new("taskkill")
        .args(&["/F", "/IM", "Termius.exe"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();
    
    println!("Waiting for process to exit...");
    thread::sleep(Duration::from_secs(2));
    Ok(())
}

// Modify JS file
fn modify_js_file(extract_dir: &Path) -> Result<bool> {
    println!("Modifying files...");
    let mut modified = false;
    
    // Find and modify main JS file
    let assets_dir = extract_dir.join("background-process").join("assets");
    
    for entry in WalkDir::new(&assets_dir).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        if path.is_file() && path.extension().map_or(false, |ext| ext == "js") {
            let file_name = path.file_name().unwrap().to_string_lossy();
            if file_name.starts_with("main-") {
                // Read file content
                let content = fs::read_to_string(path)?;
                
                // Find code to replace
                let pattern = r"const e=await this\.api\.bulkAccount\(\);";
                let re = Regex::new(pattern)?;
                
                if re.is_match(&content) {
                    // Replace code
                    let replacement = r#"
var e=await this.api.bulkAccount();
e.account.pro_mode=true;
e.account.need_to_update_subscription=false;
e.account.current_period={
    "from": "2022-01-01T00:00:00",
    "until": "2099-01-01T00:00:00"
};
e.account.plan_type="Premium";
e.account.user_type="Premium";
e.student=null;
e.trial=null;
e.account.authorized_features.show_trial_section=false;
e.account.authorized_features.show_subscription_section=true;
e.account.authorized_features.show_github_account_section=false;
e.account.expired_screen_type=null;
e.personal_subscription={
    "now": new Date().toISOString().slice(0, -5),
    "status": "SUCCESS",
    "platform": "stripe",
    "current_period": {
        "from": "2022-01-01T00:00:00",
        "until": "2099-01-01T00:00:00"
    },
    "revokable": true,
    "refunded": false,
    "cancelable": true,
    "reactivatable": false,
    "currency": "usd",
    "created_at": "2022-01-01T00:00:00",
    "updated_at": new Date().toISOString().slice(0, -5),
    "valid_until": "2099-01-01T00:00:00",
    "auto_renew": true,
    "price": 12.0,
    "verbose_plan_name": "Termius Pro Monthly",
    "plan_type": "SINGLE",
    "is_expired": false
};
e.access_objects=[{
    "period": {
        "start": "2022-01-01T00:00:00",
        "end": "2099-01-01T00:00:00"
    },
    "title": "Pro"
}];
"#;
                    
                    let new_content = re.replace(&content, replacement).to_string();
                    fs::write(path, new_content)?;
                    
                    println!("Modified file: {}", file_name);
                    modified = true;
                    break;
                }
            }
        }
    }
    
    if !modified {
        println!("Warning: Required file not found, Termius version might have been updated, please download again");
        println!("Feature configuration might not work properly");
    }
    
    Ok(modified)
}

// Disable auto update
fn disable_auto_update(base_path: &Path) -> Result<bool> {
    let update_file = base_path.join("app-update.yml");
    if update_file.exists() {
        fs::remove_file(&update_file)?;
        println!("Deleted app-update.yml, auto update disabled");
        Ok(true)
    } else {
        println!("app-update.yml not found");
        Ok(false)
    }
}

// Main function
fn main() -> Result<()> {
    println!("Termius Pro Configuration Tool");
    println!("====================================");
    
    // Ask about auto update
    println!("Disable auto-update? (y/n): ");
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    let disable_update = input.trim().eq_ignore_ascii_case("y");
    
    println!("Auto-update will be {}", if disable_update { "disabled" } else { "enabled" });
    
    // Set paths
    let home = std::env::var("USERPROFILE").context("Failed to get user home directory")?;
    let base_path = PathBuf::from(&home)
        .join("AppData")
        .join("Local")
        .join("Programs")
        .join("Termius")
        .join("resources");
    
    let asar_file = base_path.join("app.asar");
    let extract_dir = base_path.join("app");
    
    // Check if Termius is installed
    if !asar_file.exists() {
        return Err(TermiusToolError::FileNotFound(format!("File not found {}", asar_file.display())).into());
    }
    
    // Close Termius process
    kill_termius()?;
    
    // Backup original file
    let backup_file = asar_file.with_extension("asar.backup");
    if !backup_file.exists() {
        println!("Creating backup: {}", backup_file.display());
        fs::copy(&asar_file, &backup_file)?;
    }
    
    // Extract asar file
    println!("Extracting app.asar file...");
    if extract_dir.exists() {
        fs::remove_dir_all(&extract_dir)?;
    }
    
    // Use pure Rust to extract asar file
    let asar = AsarFile::from_file(&asar_file)
        .context("Failed to parse asar file")?;
    
    asar.extract_to_dir(&extract_dir)
        .context("Failed to extract asar file contents")?;
    
    println!("app.asar extracted successfully!");
    
    // Modify JS file
    modify_js_file(&extract_dir)?;
    
    // Disable auto update
    if disable_update {
        disable_auto_update(&base_path)?;
    }
    
    println!("\nComplete!");
    println!("Termius Pro has been configured");
    println!("Press Enter to exit...");
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    
    Ok(())
}